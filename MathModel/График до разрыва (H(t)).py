import numpy as np # подключаем библиотеку для работы с множествами
from scipy.integrate import odeint # импортируем функцию для интегрирования систем ОДУ
import matplotlib.pyplot as plt # подключаем библиотеку для рисования графиков
import math

fig, ax = plt.subplots() # создаём Рисунок и 1 график на нём ax
def f(x):
    return math.log(x)
ln = np.vectorize(f)

t = np.array([0, 5, 10, 15, 17, 20, 25, 30, 35, 40, 45, 49]) # Добавляем возможность делать преобразования
ax.plot(t, -0.01 * t ** 2 / 2 + 2.1/0.007 * ((1- 0.007*t)*ln(1- 0.007*t) + 0.007*t)) # рисуем график, задавая значением по оси y функцию y, а значением по оси x функцию x
plt.xlabel('t, sec') 
plt.ylabel('H, kм')
plt.grid(color = 'black') # задаём легенду осям и цвет сетки
plt.show() # Выводим на экран

