# LSHADE-SPACMA runnability smoke

Frozen archive: `LSHADE_SPACMA_1.0.zip`

The actual MATLAB smoke attempted to call `cec17_func(zeros(10,1),1)` from the extracted upstream archive. MATLAB rejected `cec17_func.mexw64` with:

`MEX file ... cec17_func.mexw64 is invalid: specified module could not be found.`

The source archive is therefore classified as `runnability=FAIL`. The presence of a MEX file is not treated as successful execution. No performance or FE claim is made for this external case.
