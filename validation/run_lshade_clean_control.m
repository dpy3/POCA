function Result = run_lshade_clean_control(project_root,output_directory)
    if nargin < 2 || isempty(output_directory)
        output_directory = pwd;
    end
    canonical_directory = fullfile(project_root,'PEGR_LSHADE_202607','algorithms','lshade_canonical');
    addpath(canonical_directory);

    population = 50;
    max_fes = 2000;
    dimension = 10;
    lower = -100;
    upper = 100;
    seed = 20260725;

    reference_fes = 0;
    reference_points = zeros(max_fes,dimension);
    rng(seed,'twister');
    timer = tic;
    [reference_score,reference_position,reference_curve] = ...
        LSHADE101_Reference(population,max_fes,lower,upper,dimension,@reference_objective);
    reference_time = toc(timer);
    reference_rng = rng;

    traced_fes = 0;
    traced_points = zeros(max_fes,dimension);
    rng(seed,'twister');
    timer = tic;
    [traced_score,traced_position,traced_curve,trace] = ...
        LSHADE101_FrozenCore(population,max_fes,lower,upper,dimension,@traced_objective);
    traced_time = toc(timer);
    traced_rng = rng;

    checks = struct();
    checks.score = isequaln(reference_score,traced_score);
    checks.position = isequaln(reference_position,traced_position);
    checks.curve = isequaln(reference_curve,traced_curve);
    checks.evaluated_points = isequaln(reference_points,traced_points);
    checks.reference_fe = reference_fes==max_fes;
    checks.traced_fe = traced_fes==max_fes;
    checks.rng = strcmp(reference_rng.Type,traced_rng.Type) ...
        && reference_rng.Seed==traced_rng.Seed ...
        && isequal(reference_rng.State,traced_rng.State);
    checks.initial_population = isequaln(trace.initial_population,traced_points(1:population,:));
    checks.trace_nonempty = ~isempty(trace.trial_vector);
    assert(all(structfun(@logical,checks)),'L-SHADE clean-control gate failed.');

    trace_json = jsonencode(struct('F',trace.F,'CR',trace.CR, ...
        'pbest_vector',trace.pbest_vector,'r1_vector',trace.r1_vector, ...
        'r2_vector',trace.r2_vector,'trial_vector',trace.trial_vector));
    Result = struct('seed',seed,'population',population,'max_fes',max_fes, ...
        'dimension',dimension,'score',traced_score,'checks',checks, ...
        'reference_seconds',reference_time,'traced_seconds',traced_time, ...
        'time_ratio',traced_time/reference_time, ...
        'serialized_trace_bytes',numel(unicode2native(trace_json,'UTF-8')), ...
        'canonical_source_zip_sha256','a9d094018b18da674849a97415116146dae6e423c19be8ef0ada9766890f0b9b');

    save(fullfile(output_directory,'lshade_clean_control_20260720.mat'),'Result','-v7');
    fprintf('LSHADE_CLEAN_CONTROL_OK=1 FEs=%d score=%.17g time_ratio=%.6f trace_bytes=%d\n', ...
        traced_fes,traced_score,Result.time_ratio,Result.serialized_trace_bytes);
    fprintf('CHECKS=%s\n',jsonencode(checks));

    function value = reference_objective(position)
        reference_fes = reference_fes+1;
        reference_points(reference_fes,:) = position;
        value = sum(position.^2);
    end

    function value = traced_objective(position)
        traced_fes = traced_fes+1;
        traced_points(traced_fes,:) = position;
        value = sum(position.^2);
    end
end
