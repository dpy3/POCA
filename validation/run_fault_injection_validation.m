function Summary = run_fault_injection_validation(output_directory)
    if nargin < 1 || isempty(output_directory)
        output_directory = pwd;
    end

    modes = {'clean','identity_name_mismatch','inherited_result_column', ...
        'candidate_overwrite','uncounted_auxiliary','post_reduction_counter', ...
        'iteration_stop','observer_rng_interference','label_operator_mismatch'};
    expected_gate = {'none','identity','identity','path','budget','budget','budget','observer','path'};
    seed = 20260724;

    records = repmat(struct(),numel(modes),1);
    for mode_index = 1:numel(modes)
        mode = modes{mode_index};
        run_on = run_minimal_de(mode,seed,true);
        run_replay = run_minimal_de(mode,seed,true);
        run_off = run_minimal_de(mode,seed,false);
        decision = audit_run(run_on,run_off,run_replay);

        records(mode_index).mode = mode;
        records(mode_index).expected_gate = expected_gate{mode_index};
        records(mode_index).decision = decision;
        records(mode_index).run = run_on;
        records(mode_index).detected = expected_failure_detected(decision,expected_gate{mode_index});
    end

    assert(records(1).decision.all_primary_gates_pass, 'Clean harness produced a false positive.');
    assert(all([records(2:end).detected]), 'At least one preregistered defect was not detected.');

    run_minimal_de('clean',seed,true);
    repetitions = 100;
    time_on = zeros(repetitions,1);
    time_off = zeros(repetitions,1);
    for repetition = 1:repetitions
        timer = tic;
        run_minimal_de('clean',seed+repetition,true);
        time_on(repetition) = toc(timer);
        timer = tic;
        run_minimal_de('clean',seed+repetition,false);
        time_off(repetition) = toc(timer);
    end

    trace_json = jsonencode(records(1).run.trace);
    overhead = struct('repetitions',repetitions, ...
        'median_logging_on_seconds',median(time_on), ...
        'median_logging_off_seconds',median(time_off), ...
        'median_time_ratio',median(time_on)/median(time_off), ...
        'clean_trace_bytes',numel(unicode2native(trace_json,'UTF-8')));

    detection_rate = mean([records(2:end).detected]);
    false_positive_rate = double(~records(1).decision.all_primary_gates_pass);
    Summary = struct('seed',seed,'records',records,'detection_rate',detection_rate, ...
        'false_positive_rate',false_positive_rate,'overhead',overhead);

    save(fullfile(output_directory,'fault_injection_results_20260720.mat'),'Summary','-v7');
    write_summary_csv(fullfile(output_directory,'fault_injection_results_20260720.csv'),records);
    fprintf('FAULT_INJECTION_OK=1 detection=%d/%d false_positive=%d time_ratio=%.6f trace_bytes=%d\n', ...
        sum([records(2:end).detected]),numel(records)-1,false_positive_rate, ...
        overhead.median_time_ratio,overhead.clean_trace_bytes);
    for mode_index = 1:numel(records)
        d = records(mode_index).decision;
        fprintf('%s expected=%s identity=%d budget=%d path=%d observer=%d detected=%d\n', ...
            records(mode_index).mode,records(mode_index).expected_gate, ...
            d.identity_pass,d.budget_pass,d.path_pass,d.observer_pass,records(mode_index).detected);
    end
end

function Run = run_minimal_de(mode,seed,logging_enabled)
    rng(seed,'twister');
    dimension = 5;
    population_size = 10;
    target_fe = 100;
    lower = -5;
    upper = 5;
    reported_fe = 0;
    true_fe = 0;
    iteration = 0;
    source_id = 'minimal_de_v1';
    declared_source_id = 'minimal_de_v1';
    result_origin = 'generated';
    stop_rule = 'fixed_true_fe';
    trace = struct('iteration',{},'target',{},'declared_source',{}, ...
        'generated_source',{},'evaluated_source',{},'evaluation_id',{}, ...
        'accepted',{},'parent_cost',{},'candidate_cost',{});
    call_counts = struct('initialization',0,'de_trial',0,'auxiliary',0);

    if strcmp(mode,'identity_name_mismatch')
        declared_source_id = 'different_algorithm_v2';
    elseif strcmp(mode,'inherited_result_column')
        result_origin = 'inherited';
    elseif strcmp(mode,'iteration_stop')
        stop_rule = 'iteration';
    end

    population = lower + (upper-lower)*rand(population_size,dimension);
    fitness = sphere_batch(population);
    true_fe = true_fe + population_size;
    reported_fe = reported_fe + population_size;
    call_counts.initialization = population_size;

    max_iterations = 9;
    while true_fe < target_fe
        if strcmp(stop_rule,'iteration') && iteration >= max_iterations
            break;
        end
        iteration = iteration + 1;
        parents_before = population_size;
        trials = zeros(population_size,dimension);
        declared_sources = repmat({'rand1'},population_size,1);
        generated_sources = repmat({'rand1'},population_size,1);
        evaluated_sources = repmat({'rand1'},population_size,1);

        for target = 1:population_size
            donors = randperm(population_size,4);
            donors(donors==target) = [];
            while numel(donors) < 3
                donors = unique([donors,randperm(population_size,3)],'stable');
                donors(donors==target) = [];
            end
            donors = donors(1:3);
            mutant = population(donors(1),:) + 0.5*(population(donors(2),:)-population(donors(3),:));
            mutant = min(max(mutant,lower),upper);
            mask = rand(1,dimension) < 0.9;
            mask(randi(dimension)) = true;
            trial = population(target,:);
            trial(mask) = mutant(mask);

            if strcmp(mode,'candidate_overwrite')
                best = population(find(fitness==min(fitness),1),:);
                trial = best + 0.3*(population(donors(1),:)-population(donors(2),:));
                trial = min(max(trial,lower),upper);
                evaluated_sources{target} = 'best1_overwrite';
            elseif strcmp(mode,'label_operator_mismatch')
                declared_sources{target} = 'local';
                generated_sources{target} = 'transfer';
                evaluated_sources{target} = 'transfer';
            end
            trials(target,:) = trial;
        end

        remaining = target_fe-true_fe;
        evaluated_count = min(population_size,remaining);
        trial_fitness = sphere_batch(trials(1:evaluated_count,:));
        evaluation_start = true_fe+1;
        true_fe = true_fe+evaluated_count;
        call_counts.de_trial = call_counts.de_trial+evaluated_count;

        for target = 1:evaluated_count
            parent_cost = fitness(target);
            candidate_cost = trial_fitness(target);
            accepted = candidate_cost <= parent_cost;
            if accepted
                population(target,:) = trials(target,:);
                fitness(target) = candidate_cost;
            end
            if logging_enabled
                if strcmp(mode,'observer_rng_interference') && target==1
                    rand();
                end
                trace(end+1) = struct('iteration',iteration,'target',target, ...
                    'declared_source',declared_sources{target}, ...
                    'generated_source',generated_sources{target}, ...
                    'evaluated_source',evaluated_sources{target}, ...
                    'evaluation_id',evaluation_start+target-1,'accepted',accepted, ...
                    'parent_cost',parent_cost,'candidate_cost',candidate_cost);
            end
        end

        if strcmp(mode,'uncounted_auxiliary') && true_fe < target_fe
            sphere_batch(mean(population,1));
            true_fe = true_fe+1;
            call_counts.auxiliary = call_counts.auxiliary+1;
        end

        if strcmp(mode,'post_reduction_counter') && population_size > 4
            [~,worst] = max(fitness);
            population(worst,:) = [];
            fitness(worst) = [];
            population_size = population_size-1;
            reported_fe = reported_fe+min(population_size,evaluated_count);
        else
            reported_fe = reported_fe+evaluated_count;
        end
    end

    [best_cost,best_index] = min(fitness);
    Run = struct('mode',mode,'logging_enabled',logging_enabled, ...
        'source_id',source_id,'declared_source_id',declared_source_id, ...
        'result_origin',result_origin,'stop_rule',stop_rule,'target_fe',target_fe, ...
        'reported_fe',reported_fe,'true_fe',true_fe,'call_counts',call_counts, ...
        'trace',trace,'best_cost',best_cost,'best_solution',population(best_index,:), ...
        'final_rng',rng,'iterations',iteration,'initial_population',parents_before);
end

function decision = audit_run(run_on,run_off,run_replay)
    identity_pass = strcmp(run_on.source_id,run_on.declared_source_id) ...
        && strcmp(run_on.result_origin,'generated');
    budget_pass = run_on.true_fe==run_on.reported_fe ...
        && run_on.true_fe==run_on.target_fe ...
        && strcmp(run_on.stop_rule,'fixed_true_fe') ...
        && sum(structfun(@double,run_on.call_counts))==run_on.true_fe;

    path_pass = true;
    if ~isempty(run_on.trace)
        path_pass = all(strcmp({run_on.trace.declared_source},{run_on.trace.generated_source})) ...
            && all(strcmp({run_on.trace.generated_source},{run_on.trace.evaluated_source})) ...
            && all([run_on.trace.evaluation_id] >= 1);
    end

    observer_pass = isequaln(run_on.best_cost,run_off.best_cost) ...
        && isequaln(run_on.best_solution,run_off.best_solution) ...
        && isequaln(run_on.reported_fe,run_off.reported_fe) ...
        && isequaln(run_on.true_fe,run_off.true_fe) ...
        && isequaln(run_on.final_rng.State,run_off.final_rng.State);
    replay_pass = isequaln(run_on.best_cost,run_replay.best_cost) ...
        && isequaln(run_on.best_solution,run_replay.best_solution) ...
        && isequaln(run_on.trace,run_replay.trace) ...
        && isequaln(run_on.final_rng.State,run_replay.final_rng.State);

    decision = struct('identity_pass',identity_pass,'budget_pass',budget_pass, ...
        'path_pass',path_pass,'observer_pass',observer_pass,'replay_pass',replay_pass, ...
        'all_primary_gates_pass',identity_pass && budget_pass && path_pass && observer_pass && replay_pass);
end

function detected = expected_failure_detected(decision,expected_gate)
    switch expected_gate
        case 'none'
            detected = decision.all_primary_gates_pass;
        case 'identity'
            detected = ~decision.identity_pass;
        case 'budget'
            detected = ~decision.budget_pass;
        case 'path'
            detected = ~decision.path_pass;
        case 'observer'
            detected = ~decision.observer_pass;
        otherwise
            error('Unknown expected gate.');
    end
end

function values = sphere_batch(points)
    values = sum(points.^2,2);
end

function write_summary_csv(filename,records)
    file_id = fopen(filename,'w');
    cleaner = onCleanup(@() fclose(file_id));
    fprintf(file_id,'mode,expected_gate,identity_pass,budget_pass,path_pass,observer_pass,replay_pass,detected\n');
    for record_index = 1:numel(records)
        d = records(record_index).decision;
        fprintf(file_id,'%s,%s,%d,%d,%d,%d,%d,%d\n',records(record_index).mode, ...
            records(record_index).expected_gate,d.identity_pass,d.budget_pass, ...
            d.path_pass,d.observer_pass,d.replay_pass,records(record_index).detected);
    end
end
