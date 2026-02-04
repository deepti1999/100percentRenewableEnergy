def goal_seek(func, x0, x1, target=0.0, tol=1e-6, max_iter=30):
    """
    Secant-method GoalSeek (legacy fallback).
    func: callable that returns the measured value for the current guess.
    x0, x1: starting guesses (x1 should differ from x0 to set direction).
    target: desired function value.
    Returns the best x found (last iterate) even if tolerance not reached.
    """
    f0 = func(x0) - target
    if abs(f0) < tol:
        return x0

    # Avoid zero step by nudging x1 if identical
    if x1 == x0:
        x1 = x0 * 1.05 if x0 != 0 else 1.0

    f1 = func(x1) - target

    for _ in range(max_iter):
        if abs(f1) < tol:
            return x1

        denominator = (f1 - f0)
        if abs(denominator) < 1e-12:
            break  # avoid divide-by-zero; return best-so-far

        x2 = x1 - f1 * (x1 - x0) / denominator

        x0, f0 = x1, f1
        x1, f1 = x2, func(x2) - target

    return x1


def binary_search_balance(gap_func, A_initial, tol=1.0, max_iter=15):
    """
    FAST Binary Search for Energy Balance.
    Gap(A) = D - R(A)
    Gap > 0 → Need MORE area | Gap < 0 → Need LESS area
    """
    gap_initial = gap_func(A_initial)
    if abs(gap_initial) <= tol:
        return A_initial
    
    # Simple fixed bracket - no slow expansion loops
    if gap_initial > 0:
        A_low, A_high = A_initial, A_initial * 2 + 1000
    else:
        A_low, A_high = max(0, A_initial * 0.1), A_initial
    
    best_A, best_gap = A_initial, abs(gap_initial)
    
    for _ in range(max_iter):
        A_mid = (A_low + A_high) / 2
        gap_mid = gap_func(A_mid)
        
        if abs(gap_mid) < best_gap:
            best_gap, best_A = abs(gap_mid), A_mid
        
        if abs(gap_mid) <= tol or abs(A_high - A_low) < 1:
            return best_A
        
        if gap_mid > 0:
            A_low = A_mid
        else:
            A_high = A_mid
    
    return best_A


def binary_search_ws_balance(balance_func, S_initial, tol=10.0, max_iter=15):
    """
    FAST Binary Search for WS Storage Balance.
    Balance > 0 → Need MORE consumption | Balance < 0 → Need LESS consumption
    """
    balance_initial = balance_func(S_initial)
    if abs(balance_initial) <= tol:
        return S_initial
    
    # Simple fixed bracket - no slow expansion loops
    if balance_initial > 0:
        S_low, S_high = S_initial, S_initial * 2 + 50000
    else:
        S_low, S_high = max(0, S_initial * 0.1), S_initial
    
    best_S, best_bal = S_initial, abs(balance_initial)
    
    for _ in range(max_iter):
        S_mid = (S_low + S_high) / 2
        bal_mid = balance_func(S_mid)
        
        if abs(bal_mid) < best_bal:
            best_bal, best_S = abs(bal_mid), S_mid
        
        if abs(bal_mid) <= tol or abs(S_high - S_low) < 1:
            return best_S
        
        if bal_mid > 0:
            S_low = S_mid
        else:
            S_high = S_mid
    
    return best_S
