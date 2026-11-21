function Result = run_external_runnability_smoke(project_root, output_directory)
    if nargin < 2 || isempty(output_directory), output_directory = fullfile(project_root,'results'); end
    lshade_directory = fullfile(project_root,'external_sources','LSHADE_SPACMA_1.0','LSHADE_SPACMA_1.0');
    addpath(lshade_directory);
    probe = zeros(10,1);
    timer = tic;
    value = cec17_func(probe,1);
    elapsed = toc(timer);
    Result = struct('case_id','external-lshade-spacma-1.0', ...
        'dependency','cec17_func.mexw64','probe_dimension',10, ...
        'function_id',1,'finite_scalar_output',isscalar(value) && isfinite(value), ...
        'elapsed_seconds',elapsed);
    assert(Result.finite_scalar_output,'CEC2017 MEX smoke failed.');
    save(fullfile(output_directory,'external_runnability_smoke.mat'),'Result');
    fprintf('EXTERNAL_LSHADE_SPACMA_SMOKE_OK=1 value=%.17g seconds=%.6f\n',value,elapsed);
end
