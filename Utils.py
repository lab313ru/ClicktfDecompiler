from math import log


def prettier_size(n, pow_=0, b=1024, u='B', pre=[''] + [p for p in 'KMGTPEZY']) -> str:
    """

    Args:
        n:
        pow_:
        b:
        u:
        pre:

    Returns:
        str: converts size in bytes to size in kb,mb and etc
    """
    r, f = min(int(log(max(n * b ** pow_, 1), b)), len(pre) - 1), '{:,.%if} %s%s'
    return (f % (abs(r % (-r - 1)), pre[r], u)).format(n * b ** pow_ / b ** float(r))