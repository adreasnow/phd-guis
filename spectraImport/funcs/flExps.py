import numpy as np

def expFunc(t: list[float], I0: int, τ: float) -> float:
    return np.multiply(np.exp(np.negative(np.divide(t, τ))), I0)

def expFuncWC(t: list[float], I0: int, τ: float, c: float) -> float:
    return np.multiply(expFunc(t, I0, τ), c)

def expFuncx2(t: list[float], I0: int, τ_1: float, c_1: float, τ_2: float, c_2: float) -> float:
    return np.add(np.multiply(expFunc(t, I0, τ_1), c_1),
                  np.multiply(expFunc(t, I0, τ_2), c_2))

def expFuncx3(t: list[float], I0: int, τ_1: float, c_1: float, τ_2: float, c_2: float, τ_3: float, c_3: float) -> float:
    return np.add(np.add(np.multiply(expFunc(t, I0, τ_1), c_1),
                         np.multiply(expFunc(t, I0, τ_2), c_2)),
                  np.multiply(expFunc(t, I0, τ_3), c_3))

def expFuncx4(t: list[float], I0: int, τ_1: float, c_1: float, τ_2: float, c_2: float, τ_3: float, c_3: float, τ_4: float, c_4: float) -> float:
    return np.add(np.add(np.add(np.multiply(expFunc(t, I0, τ_1), c_1),
                                np.multiply(expFunc(t, I0, τ_2), c_2)),
                         np.multiply(expFunc(t, I0, τ_3), c_3)),
                  np.multiply(expFunc(t, I0, τ_4), c_4))

def linFunc(t: list[float], I0: int, τ: float) -> float:
    # return np.add(np.negative(np.divide(t, τ)), np.log(I0))
    return np.multiply(np.exp(np.negative(np.divide(t, τ))), I0)

def linFuncWC(t: list[float], I0: int, τ: float, c: float) -> float:
    return np.log(np.multiply(linFunc(t, I0, τ), c))

def linFuncx2(t: list[float], I0: int, τ_1: float, c_1: float, τ_2: float, c_2: float) -> float:
    return np.log(np.add(np.multiply(linFunc(t, I0, τ_1), c_1),
                         np.multiply(linFunc(t, I0, τ_2), c_2)))

def linFuncx3(t: list[float], I0: int, τ_1: float, c_1: float, τ_2: float, c_2: float, τ_3: float, c_3: float) -> float:
    return np.log(np.add(np.add(np.multiply(linFunc(t, I0, τ_1), c_1),
                                np.multiply(linFunc(t, I0, τ_2), c_2)),
                         np.multiply(linFunc(t, I0, τ_3), c_3)))

def linFuncx4(t: list[float], I0: int, τ_1: float, c_1: float, τ_2: float, c_2: float, τ_3: float, c_3: float, τ_4: float, c_4: float) -> float:
    return np.log(np.add(np.add(np.add(np.multiply(linFunc(t, I0, τ_1), c_1),
                                       np.multiply(linFunc(t, I0, τ_2), c_2)),
                                np.multiply(linFunc(t, I0, τ_3), c_3)),
                         np.multiply(linFunc(t, I0, τ_4), c_4)))

FLFuncList = [expFuncWC, expFuncWC, expFuncx2, expFuncx3, expFuncx4]
FLLinFuncList = [linFuncWC, linFuncWC, linFuncx2, linFuncx3, linFuncx4]
