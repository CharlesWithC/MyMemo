# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

import os
import json
import telnetlib
import datetime
import time
from email import utils
import dkim

config = None
if os.path.exists("./config.json"):
    config_txt = open("./config.json","r").read()
    config = json.loads(config_txt)
    
postfix = config["postfix_host"]
host = postfix[:postfix.find(":")]
port = postfix[postfix.find(":")+1:]
mail_domain = config["mail_domain"]
mail_from = config["mail_from"]
dkim_key_path = config["dkim_key_path"]

import random
st="abcdefghjkmnpqrstuvwxy3456789ABCDEFGHJKMNPQRSTUVWXY"
def genCode(length = 8):
    ret = ""
    for _ in range(length):
        ret += st[random.randint(0,len(st)-1)]
    return ret 

icon = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAABLAAAASwCAMAAADc/0P9AAABcVBMVEVHcEzmiYlF2EX66OhE10TRJCTidXXJAAAAyQC58LnT9tP32trcXFzOFhaQ55Ag0CDh+eHs++yA5IAm0SbnjIxG2Eb99vYEygT10NDzw8PLBwdu4W4ByQEIywjMDAy68LrKAwP3/vcQzRDsoaHNERFd3V30/fQXzhfQICDkf38p0invs7PSKSncVVXtqakMzAzF88U01DRL2Uv98/O78bvZ99ln32c61TrPGhrqmpr21dWI5oj88PDQ9dAczxzM9MzjeHje+N6g66Dxu7vokZF+5H7YREThbm5443jZS0v1zc0v0y+q7arw/PDm+uaZ6pnmiIiz77Pp++nA8sDfZmb0yMjW9tZQ2lBV21XWOjrTLi6l7KXXPz/32NjVNjb77u4TzRPUMzPRJiYi0SLaUFDJ9Mn65uY+1z7plpb76+uu7q743d3urq6V6ZWD5YP44ODdX1+N54354+PywMBZ3FneYmLgamp04nTlhIRi3mK48LjLuN1wAAAAAXRSTlMAQObYZgAAMZZJREFUeNrs3d9LYlsfB+B48WK/XVieGLxQGRJM8CaV0gvJKBCErCihhG6CiCCYYCAYpr/+nPfHOWfOTM1Y7V3utZ7nP/DL+izXXj+XlgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIAFtH60M518uqs0zguFfqdzdTWs12vVer15dXXQ6RQK3VlvVLx4uN47VCt4htJ2+2T/8/hLr9eYzT4UCp3OH4m6KRRms/terzK+O76dLh8p03wOd24/V7oHw81kbuVmq/D17qKtxvCko/bF3dfzfuuyOl+sNlc63cb4+OO20j1q76RYOT+oJ69QW/vQG0x21BL+Hk9dXwx6H9ZqL45VdXjTGO1PV5Xyz0HV7n6lcJmkpnzVHU2W1ZXYLU9G3atqWrna7DSKW6W4K7o9GXdXkkzUbyrH1+saLVF+/z0M7g/KWeRq5Xw8OYuyprvF2WWSsXKnMjnVfIlqXHXcWMk4V5v98UlMY63DrVGhlryVq0ZxVzMmAhvtQbf+RrEqt3r7MUy8lC6+riVv7vK8aLWDsIPVO6i+da6G95+CztXuoFBO3stKb2LPFoKV9hdMoLkqTXrN5J2V+wNfhwQXrOE756pWCC1Xu6NONVkMK70Ti4cE4nphghVQrpZHa8lCqTdONHUCCNbVQuWq1t3fyH1Rz0atZAHpszAMkKvv7BX7ycK61GeR296qtbC5ym2fVfp8kCy4ZsURHvJm9bfWgufqstfOXVV3e7UkDzrHGyJAfmzNynnIVWuQp63wR4OrJDc2G1tiQD4GV4NhbnJVm235D/B3QLwmhWq+crU2WPyTvKe/DZMcqjXsKGWRbVcuc5ir8uzjgle1luRVfyIVLKh27r5a/nJwvLAbStvdapJnV0UT8Cygk36uc9UclVQ1o/XYsZvhWSwbx2u5z9Vmb9EudTgsDpMg1BpnMsLCOBpdBpGrare9QFUtjTeTYFTPvWPBgswJN8rhBOvmYVHGrIN6EpRqV5fF+1vtlcMKVn9Ld5VRlzVzQSnv3F3leMX96S5r+t7dVbGZBEmXxXs6HdfCDFbh+j3LejxMglVu7MkN7zQpXAs3WIVd3VVGK4YVJ3Z4e4chrWEtztfL9CAJXn0gPryx/WbwuSr33nwosNqoJjFYc8sfb+m6H0WuLotvO9c+qiWxKLjkD+OA1LXecFvWZJhEpFzxniHGAanrvtGqViSD1vcbvxKnuMYBbzUUKMUzaP3GgeuyyNZOP8JcNS+yLuvJMIlSueLqGbKzPirHGazuapZlPTpPorXyUazISLsVba5qGW4dOt5MYjazj5QsHFaqMeeqn9E6/PZNErnmvnBhmiX1+ZZxFrcoD2oJ2X5xE6Gjhlgla6nf4rDTUtX/2DwWMVK0XxeqP1RTXtQqGl796dxMFqnNXt0L1P+1Utw5dNpVz29msh4EjVRMh+L090zWKK2y3l6q5j+Hr+uyxuuNqsL0rUIqM8TrFZX8Yfjq0nde66wjSN+pp7Dx/XpNHX9Uc7qQV862b4rRjxqvnXu/Kyvi4xscTmWOl08Ln4vQo1barylr6YMKPmXYFjteqG22/cm591d8vOysqJ/PQlJ37LvlJ+5f+ll4YfNVxh/cxGj9q+j81MHLbvYbq1xGlSVmq1YHf2Xz9vllPeqr269d2kTK80ybYvNL1bGyLkplidrA9NV8q/DPOwH3WVnnde6JCuZ1OBOYOV09Z3N2T73m11oVROay586TZ0xkzf0k6KGzzs/S9EIF87g2z/Ic8+7IOjpQq6z+C4jYrW1Cz1SZp6w7NuFm9l9AxIruZnj+BPGvdzo+OJOZ2X8BEXPpyUt0fnVk16GB7P4LiNeGeeGXWTn7aV1HKvRC1Y7rG3hyXtju9peq/+x9ipn6vNyVczo87sy88CsmiJ+81W/dsPVVhmeiyWPrWLYzvOrj5YmXqjYKavM6TTcn86NdbyK8ssf6/FhZD512fv33dls8+c7UuvurPXJit2RaMAWbWwKK/ip1X74v66nt7amo3Yoo3zixvT0VvX+WddXbOGmtaUyElL9c2NeYkvtvy7p3pSCp9Vj7Yor+KnWzv8u6bZtImmsaeiz+55Pjgyk6/+t70OM4vgpJ377+Kosx1qlbxdLusVw3w9LSre/BlH39734G/VX6a4VTcY3ev60Ppq6ytHRo/1UWPVZbYCO3pb/KwGjjRhGyUHdtctza9otmwv6rjFw6CR2znboIkCtDt83Ea9v9DOTNihv9YrWnvyJ/Om5NjtOhhXfyqCu7UXKxHPnkLZ0YNTR8csp7hfHxkAu5VXU9VmwuHCAkv2rXIhyVqQ3u5FlzVYgjcmbDKPnWOhTjaJy6CZO8s7khHk7mkn93ghyJnsZO/lXd5xfJAqG2TgjqzkHHYMcCIWE4cKowfCUT7oTiXp6D19XMCcYngQ7cWCMnHGXPUoTtxIkcQjJ0nV/Itu1wJywfpDpg3p4iNK6aCdcXzZvQ1HYEO1BTbzwTnta6aAfpcKhxEyA3JodppmkTIocKg7SvZROmpr0N4dnzKD2hcjdWePqaNcFyRCc0HskhYDU3zYTl2o4GQlaQ8aAcaNIEbV/IA3KnQRO2SyuF4dh2ySihc5lfOLySQ/hsHw3FJ42Z8A09rRqGI5dgEQNnCsNwrikTg2pb2AMw0ZKJQ0va8++wqSETCbeP5l9FMyYW9ZLA59yZMzmYdycvvJtKRMrLIp9rH7VhYuIQdL61NGGiciv0OVbUgInLlTd08qt0qQETmYHc51ZP8yU2m0eCb0sD5EVP8nPqXxov8Sm73z2fptouj0d65aYx/rx/0t7eWy2V1pdKpaO9vd2Hi+Ko123l/7LHhuznUgAPe222uo3K3afJw9bW7u7O7u50a2tyPPjy9bxjOeFlBe33Pk1Xf95uTq8vxt1hnvvjM+HPoYdcjwEO7geT659d072xfFLs9b0OO39J+19un/GxVJredfN6kZrbkvOok9u+qrK/M/ev3Lsd3ei1flnTm8H0JfuTlo9/Z+9uW+JOrzgAt1m73aStGWODFGcIE3AE32SUqC+sDgqC4EOIoUnAN4KIEDAgLA3x03fLlrJLW6rJTM4591y/b5CT22vu/7mf3ldEq+uATr28rvmHtf/wCy66vZx951bV/5nlpaOvuTx4tLXZrfZPfufvv1wOp+wPa7S/2oXTf2Rncfj1Y+lktphZ3UsAFEu1e0bnD7a//u/q+opZv/oJGIdWP6dzU6rFsEaAYil16vnxGLQqOheY4Cxj5mi8Q+rtQaGl2SECSuWsUN/q/cux/tPXD1wK/dPkar8z/lE12CszzXrKgFKZL/MpeDOBJ8aPZqZ8mjU/O6k7C0ZLRc57bUNAB2vs2TyaUAHWF3vTy9WD20mOrfWNEqW13b1SSmxy765NstFwuj+lm+E330x6dJ0eFCBroYOBMhlWaF19nvSIGmyd42oy6RSYwH7iQJnkf+u5+379G9RhsDVl+0kPn32rIbb7Y/Y24fNjEBTJevqW87tvdTx17mCKelnn3/Qd0cvsfYcbEhRJ9otGV26/YTE6S1OyYriw+K2nFEe5r3TYIUGNzL0wDyg1FRhP8yrgTpXjxdQ/BmcsKJGPqZtXGwGthevm73PoBT29MMx8ouKQBRXSz7zR++JlSE1O3rXt1VonbLTtJ95I+pIGBfIqc5tlEFWV1zvtcvXiVeR4G+WdZLllpkLyjp/5UWRnr9lJ1up67IDrp+1kLXjxK3/ybhpdGsRWZq/JTlZ3MX7M3WbtQnhUNX8+Z10c/BBemt0GlwvPH2YYdCdJK/uYB9lznHQasZlidr7YmleHWd7gO9B2ly/Jdc6Bk+U13rO2Pgujv7J/WdmURwq8n5M9KW9Y6+2lqc/2RTtcLVxnGnmjjOuwvTkkpM4o4x/WTqbL1OaeNrOb4XWusXeS8d0TBwpzJ+MxwsOOGk0gy6Nsg2+wlq9KK0zInH7C61SeprvmY7aF49ArnYTjL+ES9ZAKibOn3V63QXyvrOZsznxKV6jPVEicfNthDlLW6U31xcKrrLfTbaXr9PWxkDa72UZLN2vP87L27clXg7Rj8Drb9/YHLqRNtotlurNpS7VdWay1zLOGbGK950LaJFtX7u4lrtWjus+tzuT+yplNthVrAIakWU/m1XXqaj2qOsfazP4XuJ+rXkdkSJonuQZK9qPy2zWf1DnMv3n7wDeh3CG5bsL6mL5ew4prhSsVDpuk2o/lmzDrN06qP6wK71g+XCjn1fl6ibGYas+7xyi0DhqZh+9V86o3rDEWjzOt/7gp2Rfh/20M9yE/iXWMMpuKThLd3dDzBnTKHnKiP6yL0ypVWyoFVqErf7cTHX/ao4OlmQYaLf9M/6qQV6W+bc70J6TGF2H3tlDZTuu8/7VS69Mmz33Uz+mQLx0bGr4swypLhS/eFhuSeSavQz6kS573U6stylzX8Kpb7hTvSZrTTwd8SJc074TOl1uTqdF4X6w3Jm+znINe5UO6ZDlnsnBZrnSD+QoNrIr7tbO0sbqegM6WN1bevzyj/G2s3nbFUdnPsn/UxoZsyXI37VXJ6n1MD1bR11+y7MbyPmG2JPkpe96pWb7su7E2q47LJD8FNjYky0nX1Ptrspv74oaFR35JbWxoKUk2NcyULeBNarCe1B2Zlzn6g/uMSJX3OTrDu3UruJnYq5XKL7/k6K5uMiJVclz3O1u4gtt5Vwq7pb9nBinOPvW89pUpOe7uq7097yAtWEu1B+eRJpZkbGF1L0vXcJD1FHSvU3x0pliC3aJEoiyZCHx9sl4/+rH66NzOsITt2tFMuTARaLbvvlP/DYUMb1KcUyJPTk0ExpHLbkawGjhVcpJhv/s6J9LkQ4aJQAPLMD8m9Gq+hQH6Cfzyi2Q4FH/dQB3XE25taOLd4rkEBwk+cyJNVk2wGlq8+PWe0TZG6IGpqvw7/QQTg1dNVHI33RTrQxtDdC7+urbuKSmSJMFdWBeNlHLDBKvZLtZrUiTJlglWq1OsZjrFJ/GF/UiKJHkfPhaW+2qprsnbg14nzJIVP15jy8gm98nkUfgmtxVS6Ln/a5P7XDvVzHT3aEt1/c2D6GouuLDBpODnbDRUzdeJwFpqaZjG724esSJF4g/tbrdUzsd5wBo2NU7Dn1W11z1Hwve5t3Wb4xN7GiaT8M2jn1iRIjN+ucaZTpqdDTdtjdPd6Lb7DCtMtX/Ki+O26rmm5T6ZRK9nLLMiQ8LvltlorKAfkoDV3JVz4ffiOpyTIQ+1hsecHC96/HDWWl3noj+2n9EiQaJf1NtprqKfU3jVO26usNEf27O08Of1w6I560TS4EmS6A04lgkzJHqR8LK9ki5nAOusvboeB1+V7CGKDAne6LjTYEkzXDKzcNxgYYOP5xzSIkGCO5mLDZb0NgFYV/qtY89zWsSnE/yHddtgTfsJXnlp8uHPt8FFPeZFeIKvG+01eQT+aTxY202O1seKOu0JXnlZa7Kos+FeNborO7g7+IEX4dm3tWX8WQ8Ha6nN0XoUW9UbXoQn+OrZRt/TDb9j5lWbdQ0+R7bIi/DEnig99zMwmbxttLAXGhhTnh1b8SaQ62Cvml2Aj/0lcK17fGK3YW01WtVHwWA1OxV45YNgutOP/cMatlrX4JeKm31DL/aXoAuM6BzHnh9p9iGS4J1Y7b5SHLsnd44YwZkL/f9v93DWQSxYnWYLe2hRe6oTu07c7qrLWezMtd0BG9t1HxIjOLFHCTearWtsr6Xh5nDs+efXxAjObuj/f7svvQ1CH0/rtTtgnxmwU53YQyQP2y3sI2A1+EmwRYyp/nQBlh7WfRO6cXCVGMHZBlaLvwQNj9jQ+6d3iBGcS2A1CNbzQbuFDW0OnhMjOENgNQjW44ZHbOg7tS5Jjs4bYAGrVEIfUXtBjOC8BBaw/MQCC1jAAlZzTYweMYAFLGDdIyNgAQtYwFLYKd/gBixgAWv8WQcWsIAFrCoJPf3qBj9gAQtYwBJgAavJxJ5+JgawgAWsMmD1kQEsYAGrCljHyAAWsIBVBaxTZAALWMAClgALWMDySQgsYAFL012ABSxgJQeLGMACFrDuERtHgQUsYAELWMACFrDGnbeRhXX4GVjAAtZ9EvrOk/uwgAUsYN0nLvADFrCAVSauSAYWsIBVJh6hABawgFUmt8ACFrCAVSUeUp3qeEgVWLVyFlnYZWJMcwsTWMC6d15FFnaHGMG5BBawSmVWYac5I2ABC1h3zTwxpvnvClgTygWwJpMVYgTnLbCABay75pAYwdkFlk9CYN01q8QITgdYwALWXbNJjOCcAAtYwLprrogRnDlgAQtYd80MMYJzDCxgAQtYVdIHFrCABawyARawgAWsMukBC1jAAlaVPAcWsIAFrCpZBhawgAWsKnkMLGABC1hVsgIsYAELWFWyCixgAQtYVbIJLGABC1hVMgMsYAELWFXyAFjAAhawgAUsYAFLgAUsYAELWMACFrCABSxgAQtYAixgAQtYwAIWsIAFLGABC1jAEmABC1jAAhawgAUsYAELWMAClgALWMACFrCABSxgAQtYwAIWsARYwAIWsIAFLGABS4AFLGABS4AFLGABC1jAAhawBFjAAhawBFjAAhawgAUsYAFLgAUsYAFLgAUsYAELWMACFrAEWMACFrAEWMACFrCABSxgAUuABSxgAQtYwAIWsIAFLGABC1gCLGABC1jAAhawgAUsYAELWMASYAELWMACFrCABSxgAQtYwAKWAAtYwAIWsIAFLGABC1jAAhawBFjAAhawgAUsYAELWMACFrCAJcACFrCABSxgAQtYAixgAQtYAixgAQtYwAIWsIAlwAIWsIAlwAIWsIAFLGABC1gCLGABC1gCLGABC1jAAhawgCXAAhawgCXAAhawgAUsYAELWAIsYAELWMACFrCABSxgAQtYwBJgAQtYwAIWsIAFLGABC1jAApYAC1jAAhawgAUsYAELWMACFrAEWMACFrCABSxgAQtYwAIWsIAlwAIWsIAFLGABC1jAAhawgAUsARawgAUsYAELWMASYAELWMASYAELWMACFrCABSwBFrCABSwBFrCABSxgAQtYwBJgAQtYwBJgAQtYwAIWsIAFLAEWsIAFLAEWsIAFLGABC1jAEmABC1jAAhawgAUsYAELWMAClgALWMACFrCABSxgAQtYwAIWsARYwAIWsIAFLGABC1jAAhawgCXAAhawgAUsYAELWMACFrCABSwBFrCABSxgAQtYwAIWsIAFLGAJsIAFLGABC1jAApYAC1jAApYAC1jAAhawgAUsYAmwgAUsYAmwgAUsYAELWMAClgALWMAClgALWMACFrCABSxgCbCABSxgCbCABSxgAQtYwAKWAAtYwAIWsIAFLGABC1jAAhawBFjAAhawgAUsYAELWMACFrCAJcACFrCABSxgAQtYwAIWsIAFLAEWsIAFLGABC1jAAhaw/htYf/1jYP4OLGDdE6zvIwfsd8CKBuu73wfmT8AC1j3B+l3kgP0DsIAFLGABC1jACgXrb38OzF+ABSxgAeseYP02sq7fAwtYwAIWsIAFLGABC1jAAhawgAUsYAELWP9g1/5ZEozCOAyPLwRGFokamJBD4GK0hNTaH4dwapBsaJCsIXAo6tMH7dIZTjycw3V/hB+c61kOsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCAlaezisH6BhawgJUdrIfIXfcrBmsPWMACVnaw2sACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYP3Wz7rrK7CABSxg/WNZd90FFrCABSxgAQtYwAIWsIAFLGABK6DPisGaAAtYwKoLrKOKwToGFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGAVA1Z7J7B7YAELWMAqNWABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAUsYAELWMACFrCABSxgAQtYwAIWsIAFLGABC1jAAhawgAWsoL4OApsAC1jAAlapAQtYwAIWsIAFLGAJWMACFrCABSxgbenqMLBbYAlYwCo1YAELWMACFrCABSxgAUvAAhawgAUsYAELWMACFrCABSwBC1jAAhawgAUsYAELWMACFrAELGABC1jAAhawgAUsYAELWMASsIAFLGABC1jAAhawgAUsYAFLwAIWsIAFLGABC1gCFrCABSwBC1jAAhawgAUsYAlYwAIWsAQsYAELWMACFrCAJWABC1jAErCABSxgAQtYwAKWgAUsYAFLwAIWsIAFLGABC1gCFrCABSxgAQtYwAIWsIAFLGAJWMACFrCABSxgAQtYwAIWsIAlYAELWMACFrCABSxgAQtYwAKWgAUsYAELWMACFrCABSxgAQtYAhawgAUsYAELWMACBrCABSxgCVjAAhawgAUsYAFLwAIWsIAlYAELWMACFrCABSwBC1jAApaABSxgAQtYwAIWsAQsYAELWAIWsIAFLGABC1jAErCABSxgCVjAAhawgAUsYAFLwAIWsIAFLGABC1jAAhawgAUsAQtYwAIWsIAFLGBtbQ0MYAELWKWA1QEGsIAFLGApsQ6wgAUsYBUTsIAFLGABC1jAApaABSxgAQtYwAIWsIAFLGABC1gCFrCABSxgAQtYwAIWsIAFLGAJWMACFrCABSxgAQtYwAIWsIAlYAELWMACFrCABSxgAQtYwAKWgAUsYAELWMACFrAELGABC1gCFrCABSxgAQtYwBKwgAUsYAlYwAIWsIAFLGABS8ACFrCAJWABC1jAAhawgAUsAQtYwAKWgAUsYAELWMACFrAELGABC1jAAhawgAUsYAELWMASsIAFLGABC1jAAhawgAUsYAFLWboEFrCABaxSWgMLWMBK7BwY0W2ABSxgJbYGRnTvwAIWsBJbASO6JbCABazE3oAR3RRYwAJWYktgRNcFFrCAlVgXGMACFrBKAWsGDGABC1ilgNUDBrCABSxgCVjAAhawgJWxIbCABSyVAlYfWMAClkoBawAsYAFLpYA1AhawgKVSwGoBC1jAErCABSxgAQtYwAKWgAUsYAFLwAIWsIAFLGABC1gCFrCABSwBC1jAAhawgAUsYAlYwAIWsAQsYAELWMACFrCAJWABC1jAErCABSxgAQtYwAKWgAUsYAELWMACFrCABSxgAQtYAhawgAUsYAELWMACFrCABSxgCVjAAhawgAUsYAELWMACFrCAJWABC1jAAhawgAUsYAELWMACloAFLGABC1jAAhawgAUsYAELWAJWdHNgAUvAKqUFsIAlYAHrz4ajRQ9YwAIWsNJ7ity1mQMLWMACVnqtULA+gAUsYAEruU6oV80dsIAFLGAlN40F6xlYwAIWsJIbx4I17AALWMACVmovsWA1s2qXPQUWsICVu5tgsE6qXfYCWMACVu4eg8Gq9+voCFjAAlbuWsFgXVe77ABYwAJW5jbBXlV8CobAApZnlblxNFjNstJlVw2wgBXVD3tn85rY0sThG0LmLKK7QaILOaALxY+N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"

def telnetMail(mail_from, mail_to, mail_from_name, mail_to_name, subject, plain, html):
    tn = telnetlib.Telnet(host, port)
    tn.read_until(b"220")
    tn.write(b"HELO charles14.xyz\n")
    tn.read_until(b"250")
    boundary = genCode()
    nowdt = datetime.datetime.now()
    nowtuple = nowdt.timetuple()
    nowtimestamp = time.mktime(nowtuple)
    ts = utils.formatdate(nowtimestamp)

    msgdata = f"""MIME-Version: 1.0
From: {mail_from_name} <{mail_from}>
To: {mail_to_name} <{mail_to}>
Date: {str(ts)}
Message-ID: {utils.make_msgid()}
Subject: {subject}

Content-type: text/html;boundary="{boundary}";charset=utf-8

{html}

--{boundary}

Content-Type: text/plain;charset=utf-8

{plain}

"""

    if not dkim_key_path == "" and os.path.exists(dkim_key_path):
        dkim_pvtkey = open(dkim_key_path).read()
        headers = [b"MIME-Version",b"To", b"From", b"Subject", b"Message-ID", b"Content-type"]
        sig = dkim.sign(
            message=msgdata.encode(),
            selector=b"selector1",
            domain=mail_domain.encode(),
            privkey=dkim_pvtkey.encode(),
            include_headers=headers,
        )
        msgdata = f"""MIME-Version: 1.0
From: {mail_from_name} <{mail_from}>
To: {mail_to_name} <{mail_to}>
Date: {str(ts)}
Message-ID: {utils.make_msgid()}
Subject: {subject}
Content-type: text/html;charset=utf-8
DKIM-Signature: {sig[len("DKIM-Signature: ") :].decode()}

{html}

"""

    s=f"""MAIL FROM: <{mail_from}>
RCPT TO: <{mail_to}>
DATA
{msgdata}

.

"""

    nowait = False
    for ss in s.split("\n"):
        if ss == "DATA":
            nowait = True
        if ss == ".":
            nowait = False
        tn.write((ss+"\n").encode())
        if str(tn.read_very_eager().decode()).find("queued") != -1:
            return
        if not nowait:
            tn.read_until(b"250")

def sendVerification(mail_to, username, vtype, note, expire, link):
    data = "<!DOCTYPE html><html>\n"
    data += "<head><style>h2{font-size:1.6em} p{font-size:1.2em}</style></head>\n"
    data += "<body><div style='margin:auto;text-align:center'>\n"
    data += f"<h1 style='font-size:2.6em'><a href='https://memo.charles14.xyz' style='text-decoration:none'><img src='{icon}' style='width:0.8em;height:0.8em' alt=""></a> My Memo</h1>\n"
    data += f"<h2>{vtype}</h2>\n"
    data += f"<p font-size='1.2em'>{note}</p>\n"
    if expire != -1:
        data += f"<p style='font-size:1em'>The link will expire in {expire}.</p>\n"
    data += f"<p style='font-size:1.2em'><a href='{link}' style='display:inline-block;background:#4444ff;border-radius:0.5em;padding:0.4em;padding-left:0.8em;padding-right:0.8em;color:white;text-decoration:none'>Click to open verification link</a></p><br>\n"
    data += f"<p style='font-size:1em'>If the link above doesn't work, please copy the link below and paste it in your browser to open it.</p>\n"
    data += f"<p style='font-size:1em'>{link}</p>\n"
    data += f"<br><br><hr>\n"
    data += f"<p style='font-size:0.6em;color:gray'>This is an automated email. Please do not reply to it. To contact, use <a href='mailto:memo@charles14.xyz'>memo@charles14.xyz</a>.</p>\n"
    data += f"<p style='font-size:0.6em;color:gray'>Copyright &copy; 2021 My Memo | Developed by Charles</a></p>\n"
    data += "</div></body></html>\n"

    plain = "My Memo\n"
    plain += vtype.replace("<br>","\n").replace("\n\n","\n") + "\n"
    plain += "Verification link: " + link + "\n"
    plain += "The link will expire in " + expire + "\n"
    plain += "\n"
    plain += "This is an automated email. Please do not reply to it. To contact, use memo@charles14.xyz .\n"
    plain += "Copyright &copy; 2021 My Memo | Developed by Charles."

    telnetMail(mail_from, mail_to, "My Memo", username, vtype, plain, data)

def sendNormal(mail_to, username, subject, content):
    data = "<!DOCTYPE html><html>\n"
    data += "<head><style>h2{font-size:1.6em} p{font-size:1.2em}</style></head>\n"
    data += "<body><div style='margin:auto;text-align:center'>\n"
    data += f"<h1 style='font-size:2.6em'><a href='https://memo.charles14.xyz' style='text-decoration:none'><img src='{icon}' style='width:0.8em;height:0.8em' alt=""></a> My Memo</h1>\n"
    data += f"<h2>{subject}</h2>\n"
    data += f"<p font-size='1.2em'>{content}</p>\n"
    data += f"<br><br><hr>\n"
    data += f"<p style='font-size:0.6em;color:gray'>This is an automated email. Please do not reply to it. To contact, use <a href='mailto:memo@charles14.xyz'>memo@charles14.xyz</a>.</p>\n"
    data += f"<p style='font-size:0.6em;color:gray'>Copyright &copy; 2021 My Memo | Developed by Charles</a></p>\n"
    data += "</div></body></html>\n"

    plain = "My Memo\n"
    plain += subject.replace("<br>","\n").replace("\n\n","\n") + "\n"
    plain += content.replace("<br>","\n").replace("\n\n","\n") + "\n"
    plain += "\n"
    plain += "This is an automated email. Please do not reply to it. To contact, use memo@charles14.xyz .\n"
    plain += "Copyright &copy; 2021 My Memo | Developed by Charles."
    
    telnetMail(mail_from, mail_to, "My Memo", username, subject, plain, data)    