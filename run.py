# -*- coding: utf-8 -*

import sys
from gls_winexp_check import GLSWinEXPCheck

def main():
    window = GLSWinEXPCheck()
    window.mainloop()
    return 0

if __name__ == "__main__":
    sys.exit(main())