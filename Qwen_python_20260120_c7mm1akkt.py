from scipy.optimize import newton

def calculate_ytm(price, coupon, face, years):
    def ytm_func(r):
        return sum(coupon / (1 + r)**t for t in range(1, years+1)) + face / (1 + r)**years - price
    try:
        return round(newton(ytm_func, 0.1) * 100, 2)
    except:
        return None

def calculate_sharpe(portfolio_return, risk_free, volatility):
    return round((portfolio_return - risk_free) / volatility, 2)

def calculate_pe(price, eps):
    return round(price / eps, 2)