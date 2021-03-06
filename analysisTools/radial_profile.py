import numpy as np

def div_nonzero(a, b):
    m = b != 0
    c = np.zeros_like(a)
    c[m] = a[m] / b[m].astype(a.dtype)
    return c

def make_radial_profile(image, x, y, mask = None, rs = None):
    """
    """
    if rs is None :
        rs = np.round(np.sqrt(x**2 + y**2), 0).astype(np.uint16).ravel()
    
    if mask is None :
        mask = np.ones_like(image, dtype=np.bool) 
    m = mask.ravel().astype(np.bool)
    
    r_count = np.bincount(rs[m], minlength=rs.max()+1)
    r_int   = np.bincount(rs[m], image.ravel()[m].astype(np.float),  minlength=rs.max()+1)
    #print('r_count.shape, r_int.shape', r_count.shape, r_int.shape, m.shape, rs.shape)
    return div_nonzero(r_int, r_count), rs

