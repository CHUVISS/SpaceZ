import numpy as np # подключаем библиотеку для работы с множествами
from scipy.integrate import odeint # импортируем функцию для интегрирования систем ОДУ
import matplotlib.pyplot as plt # подключаем библиотеку для рисования графиков
import math

fig, ax = plt.subplots() # создаём Рисунок и 1 график на нём ax
def f(x):
    return math.log(x)
ln = np.vectorize(f)


w = 0.007 #мю
u = 2.1 #скорость выхода топлива
g = 0.01 #ускорение свободного падения км/с
t = np.array([0, 5, 10, 15, 17, 20, 25, 30, 35, 40, 45, 49]) # Добавляем возможность делать преобразования
ax.plot(t, -g * t ** 2 / 2 + u/w * ((1- w*t)*ln(1- w*t) + w*t)) # рисуем график, задавая значением по оси y функцию y, а значением по оси x функцию x
plt.xlabel('t, c') 
plt.ylabel('H, км')
plt.grid(color = 'black') # задаём легенду осям и цвет сетки
plt.show() # Выводим на экран

