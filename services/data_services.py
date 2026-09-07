#////////////////////////////////////////////////////////////
#
# By: Rafael Miguel M. Vieira
# Projct made with: Qt Designer and Pyside6
# Version: 1.0.0
#
# This project can be used for study and improvement. Since this 
# is my first Python code, I want it serve as an example in the 
# future so I can see my mistakes and learn from them.
# 
# there are limitations o Qt Licenses if you want to use your products
# commercially, I recommend reading them on the official website:
# https://doc.qt.io/qtfopython/licenses.html
#
#////////////////////////////////////////////////////////////

from datetime import datetime
import locale

try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')
    except:
        pass

def obter_data_atual():
    agora = datetime.now()
    return {
        "dia": agora.strftime("%d"),
        "mes": agora.strftime("%B").capitalize(),
        "semana": agora.strftime("%A").capitalize(),
        "ano": agora.strftime("%Y")
    }