import numpy as np # подключаем библиотеку для работы с множествами
from scipy.integrate import odeint # импортируем функцию для интегрирования систем ОДУ
import matplotlib.pyplot as plt # подключаем библиотеку для рисования графиков
import math

fig, ax = plt.subplots() # создаём Рисунок и 1 график на нём ax
def f(x):
    return math.log(x)
f2 = np.vectorize(f)

w = 0.0068 #мю
u = 2.1 #скорость вылета топлива (км/с)
g = 0.01 #ускорение свободного падения (км/с^2)

t = np.array([0, 15, 25, 35, 45, 49]) # Добавляем возможность делать преобразования
ax.plot(t, -g * t + u * f2(1/(1 - w*t))) # рисуем график, задавая значением по оси y функцию y, а значением по оси x функцию x
plt.xlabel('t, sec') 
plt.ylabel('U, kм/sec')
plt.grid(color = 'black') # задаём легенду осям и цвет сетки
plt.show() # Выводим на экран
