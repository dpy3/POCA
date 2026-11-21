function Result = run_lshade_positive_external_case(project_root,output_directory)
    if nargin < 2 || isempty(output_directory), output_directory = fullfile(project_root,'results'); end
    canonical_directory = fullfile(fileparts(project_root),'PEGR_LSHADE_202607','algorithms','lshade_canonical');
    addpath(canonical_directory);
    if ~exist(output_directory,'dir'), mkdir(output_directory); end

    tasks = {'sphere','rosenbrock','rastrigin'};
    seeds = 20260741:20260743;
    record_cells = cell(numel(tasks)*numel(seeds),1);
    record_index = 0;
    for task_index = 1:numel(tasks)
        for seed_index = 1:numel(seeds)
            record_index = record_index+1;
            record_cells{record_index} = run_one(tasks{task_index},seeds(seed_index));
            assert(record_cells{record_index}.all_pass,'L-SHADE positive external gate failed.');
        end
    end
    records = vertcat(record_cells{:});

    Result = struct('protocol','LSHADE101_POSITIVE_EXTERNAL_20260721', ...
        'source_sha256','a9d094018b18da674849a97415116146dae6e423c19be8ef0ada9766890f0b9b', ...
        'records',records,'pass_count',sum([records.all_pass]), ...
        'record_count',numel(records),'false_positive_count',sum(~[records.all_pass]));
    save(fullfile(output_directory,'lshade_positive_external_20260721.mat'),'Result','-v7');
    write_csv(fullfile(output_directory,'lshade_positive_external_20260721.csv'),records);
    file_id = fopen(fullfile(output_directory,'lshade_positive_external_20260721.json'),'w');
    cleaner = onCleanup(@() fclose(file_id));
    fprintf(file_id,'%s',jsonencode(Result,'PrettyPrint',true));
    fprintf('LSHADE_POSITIVE_EXTERNAL_OK=1 pass=%d/%d\n',Result.pass_count,Result.record_count);
end

function Record = run_one(task_id,seed)
    population = 50; max_fes = 5000; dimension = 10; lower = -5; upper = 5;
    reference_fes = 0; traced_fes = 0; replay_fes = 0;
    reference_points = zeros(max_fes,dimension);
    traced_points = zeros(max_fes,dimension);

    rng(seed,'twister'); timer = tic;
    [reference_score,reference_position,reference_curve] = ...
        LSHADE101_Reference(population,max_fes,lower,upper,dimension,@reference_objective);
    reference_seconds = toc(timer); reference_rng = rng;

    rng(seed,'twister'); timer = tic;
    [traced_score,traced_position,traced_curve,trace] = ...
        LSHADE101_FrozenCore(population,max_fes,lower,upper,dimension,@traced_objective);
    traced_seconds = toc(timer); traced_rng = rng;

    rng(seed,'twister');
    [replay_score,replay_position,replay_curve,replay_trace] = ...
        LSHADE101_FrozenCore(population,max_fes,lower,upper,dimension,@replay_objective);
    replay_rng = rng;

    checks = struct();
    checks.score = isequaln(reference_score,traced_score,replay_score);
    checks.position = isequaln(reference_position,traced_position,replay_position);
    checks.curve = isequaln(reference_curve,traced_curve,replay_curve);
    checks.evaluated_points = isequaln(reference_points,traced_points);
    checks.fe = reference_fes==max_fes && traced_fes==max_fes && replay_fes==max_fes;
    checks.rng = same_rng(reference_rng,traced_rng) && same_rng(traced_rng,replay_rng);
    checks.initial_population = isequaln(trace.initial_population,traced_points(1:population,:));
    checks.candidate_path = isequaln(trace.trial_vector,traced_points(population+1:end,:));
    checks.trace_replay = isequaln(trace,replay_trace);
    all_pass = all(structfun(@logical,checks));
    trace_bytes = numel(unicode2native(jsonencode(struct('F',trace.F,'CR',trace.CR, ...
        'trial_vector',trace.trial_vector,'trial_fitness',trace.trial_fitness, ...
        'success',trace.success)),'UTF-8'));
    Record = struct('case_id',['external-lshade101-' task_id '-' num2str(seed)], ...
        'source_id','LSHADE-1.0.1-author-corrected','source_sha256','a9d094018b18da674849a97415116146dae6e423c19be8ef0ada9766890f0b9b', ...
        'runner_id','positive-external-case-v1','logging_mode','full_candidate', ...
        'task_id',task_id,'seed',seed,'population',population,'dimension',dimension, ...
        'target_fe',max_fes,'true_fe',traced_fes,'reported_fe',trace.final_fes, ...
        'score',traced_score,'reference_seconds',reference_seconds, ...
        'traced_seconds',traced_seconds,'runtime_ratio',traced_seconds/reference_seconds, ...
        'trace_bytes',trace_bytes,'checks',checks,'all_pass',all_pass, ...
        'identity','PASS','budget','PASS','path','PASS','observer','PASS', ...
        'replay','PASS','runnability','PASS','decision','PASS');

    function value = reference_objective(position)
        reference_fes = reference_fes+1; reference_points(reference_fes,:) = position;
        value = evaluate_task(task_id,position);
    end
    function value = traced_objective(position)
        traced_fes = traced_fes+1; traced_points(traced_fes,:) = position;
        value = evaluate_task(task_id,position);
    end
    function value = replay_objective(position)
        replay_fes = replay_fes+1; value = evaluate_task(task_id,position);
    end
end

function value = evaluate_task(task_id,position)
    switch task_id
        case 'sphere'
            value = sum(position.^2);
        case 'rosenbrock'
            value = sum(100*(position(2:end)-position(1:end-1).^2).^2 + (position(1:end-1)-1).^2);
        case 'rastrigin'
            value = 10*numel(position)+sum(position.^2-10*cos(2*pi*position));
        otherwise
            error('Unknown task.');
    end
end

function result = same_rng(first,second)
    result = strcmp(first.Type,second.Type) && first.Seed==second.Seed && isequal(first.State,second.State);
end

function write_csv(filename,records)
    file_id = fopen(filename,'w'); cleaner = onCleanup(@() fclose(file_id));
    fprintf(file_id,'case_id,task_id,seed,target_fe,true_fe,reported_fe,score,runtime_ratio,trace_bytes,all_pass\n');
    for index = 1:numel(records)
        row = records(index);
        fprintf(file_id,'%s,%s,%d,%d,%d,%d,%.17g,%.9f,%d,%d\n',row.case_id,row.task_id, ...
            row.seed,row.target_fe,row.true_fe,row.reported_fe,row.score,row.runtime_ratio,row.trace_bytes,row.all_pass);
    end
end
