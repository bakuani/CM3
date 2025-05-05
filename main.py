import tkinter as tk
from tkinter import ttk, messagebox
import math
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class ImproperIntegralAnalyzer:
    @staticmethod
    def check_convergence(f, a, b, break_points, eps=1e-6, max_iter=100):
        total = 0.0
        try:
            points = sorted([a, b] + break_points)
            for i in range(len(points) - 1):
                left, right = points[i], points[i + 1]
                delta = 0.1
                prev = None
                for _ in range(max_iter):
                    l = left + delta if left in break_points else left
                    r = right - delta if right in break_points else right
                    part = IntegralMethods.trapezoid(f, l, r, 1000)
                    if prev and abs(part - prev) < eps:
                        total += part
                        break
                    prev = part
                    delta *= 0.5
                else:
                    return False, total
            return True, total
        except:
            return False, None


class IntegralMethods:
    @staticmethod
    def rectangle(f, a, b, n, mode='middle'):
        h = (b - a) / n
        result = 0.0
        for i in range(n):
            if mode == 'left':
                x = a + i * h
            elif mode == 'right':
                x = a + (i + 1) * h
            else:
                x = a + (i + 0.5) * h
            result += f(x)
        return result * h

    @staticmethod
    def trapezoid(f, a, b, n):
        h = (b - a) / n
        sum_val = sum(f(a + i * h) for i in range(1, n))
        return h * (0.5 * (f(a) + f(b)) + sum_val)

    @staticmethod
    def simpson(f, a, b, n):
        if n % 2 != 0:
            n += 1
        h = (b - a) / n
        sum_odd = 0.0
        sum_even = 0.0
        for i in range(1, n // 2 + 1):
            sum_odd += f(a + (2 * i - 1) * h)
        for i in range(1, n // 2):
            sum_even += f(a + 2 * i * h)
        return h / 3 * (f(a) + f(b) + 4 * sum_odd + 2 * sum_even)

    @staticmethod
    def adaptive_integrate(f, a, b, method, break_points, eps=1e-6, max_iter=100):
        result = 0.0
        points = sorted([a, b] + break_points)
        for i in range(len(points) - 1):
            left, right = points[i], points[i + 1]
            if left in break_points:
                delta = 1e-6
                prev = None
                for _ in range(max_iter):
                    part = method(f, left + delta, right)
                    if prev and abs(part - prev) < eps:
                        result += part
                        break
                    prev = part
                    delta *= 0.5
                else:
                    raise ValueError("Интеграл расходится")
            elif right in break_points:
                delta = 1e-6
                prev = None
                for _ in range(max_iter):
                    part = method(f, left, right - delta)
                    if prev and abs(part - prev) < eps:
                        result += part
                        break
                    prev = part
                    delta *= 0.5
                else:
                    raise ValueError("Интеграл расходится")
            else:
                result += method(f, left, right, 1000)
        return result


class FunctionEvaluator:
    def __init__(self):
        self.functions = [
            {'func': lambda x: -x ** 3 - x ** 2 + x + 3, 'desc': '-x³ -x² +x +3'},
            {'func': lambda x: 1 / math.sqrt(x) if x != 0 else float('inf'), 'desc': '1/√x (x=0 - разрыв)'},
            {'func': lambda x: 1 / (1 - x) if x != 1 else float('inf'), 'desc': '1/(1-x) (x=1 - разрыв)'}
        ]

    def get_function(self, index):
        return self.functions[index]['func']


class IntegrationTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.func_eval = FunctionEvaluator()
        self._setup_ui()

    def _setup_ui(self):
        ttk.Label(self, text="Функция:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.func_combo = ttk.Combobox(
            self,
            values=[f['desc'] for f in self.func_eval.functions],
            state="readonly"
        )
        self.func_combo.current(0)
        self.func_combo.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        input_fields = [
            ('a', 1), ('b', 2), ('Точность ε', 3), ('Начальное n', 4)
        ]
        for text, row in input_fields:
            ttk.Label(self, text=f"{text}:").grid(row=row, column=0, padx=10, pady=5, sticky="w")
            entry = ttk.Entry(self)
            entry.grid(row=row, column=1, padx=10, pady=5)
            setattr(self, f'{text}_entry', entry)

        ttk.Label(self, text="Метод:").grid(row=5, column=0, padx=10, pady=5, sticky="w")
        self.method_combo = ttk.Combobox(
            self,
            values=[
                "Прямоугольники (левые)",
                "Прямоугольники (правые)",
                "Прямоугольники (средние)",
                "Трапеции",
                "Симпсон"
            ],
            state="readonly"
        )
        self.method_combo.current(2)
        self.method_combo.grid(row=5, column=1, padx=10, pady=5)

        self.calc_btn = ttk.Button(self, text="Вычислить", command=self._calculate)
        self.calc_btn.grid(row=6, column=0, columnspan=2, pady=10)

        self.result_text = tk.Text(self, height=10, width=60, state="disabled")
        self.result_text.grid(row=7, column=0, columnspan=2, padx=10, pady=10)

        ttk.Label(self, text="Точки разрыва (через ;):").grid(row=8, column=0, padx=10, pady=5, sticky="w")
        self.break_entry = ttk.Entry(self)
        self.break_entry.grid(row=8, column=1, padx=10, pady=5)

        self.figure = Figure(figsize=(6, 4), dpi=100)
        self.plot = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().grid(row=0, column=2, rowspan=9, padx=10, pady=10)

    def _calculate(self):
        try:
            a = float(self.a_entry.get().replace(',', '.'))
            b = float(self.b_entry.get().replace(',', '.'))
            eps = float(getattr(self, 'Точность ε_entry').get().replace(',', '.'))
            n0 = int(getattr(self, 'Начальное n_entry').get())
            func = self.func_eval.get_function(self.func_combo.current())
            break_points = [float(x.strip()) for x in self.break_entry.get().split(';') if x.strip()]

            converges, _ = ImproperIntegralAnalyzer.check_convergence(func, a, b, break_points)
            if not converges:
                messagebox.showwarning("Результат", "Интеграл не существует")
                return

            method = self._get_selected_method()
            result = IntegralMethods.adaptive_integrate(
                func, a, b, method, break_points, eps
            )

            self.result_text.config(state="normal")
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END,
                                    f"Значение интеграла: {result:.8f}\n"
                                    f"Точность: ε = {eps:.1e}\n"
                                    f"Число разбиений: {n0}\n")
            self.result_text.config(state="disabled")

            self._plot_function(func, a, b)

        except ValueError as ve:
            if "расходится" in str(ve):
                messagebox.showwarning("Результат", "Интеграл не существует")
            else:
                messagebox.showerror("Ошибка", str(ve))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка вычислений: {str(e)}")

    def _get_selected_method(self):
        method_idx = self.method_combo.current()
        if method_idx < 3:
            return lambda f, a, b, n: IntegralMethods.rectangle(f, a, b, n, ['left', 'right', 'middle'][method_idx])
        elif method_idx == 3:
            return lambda f, a, b, n: IntegralMethods.trapezoid(f, a, b, n)
        else:
            return lambda f, a, b, n: IntegralMethods.simpson(f, a, b, n)

    def _plot_function(self, f, a, b):
        num_points = 400
        x = [a + i * (b - a) / (num_points - 1) for i in range(num_points)]
        y = [f(xi) if not math.isinf(f(xi)) else None for xi in x]

        ax = self.plot
        ax.clear()
        ax.plot(x, y, label="f(x)")
        ax.fill_between(x, y, alpha=0.3)
        ax.set_xlabel("x")
        ax.set_ylabel("f(x)")
        ax.set_title("График функции")
        ax.legend()
        ax.grid()
        self.canvas.draw()


class IntegralCalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Численное интегрирование")
        self.geometry("1200x800")
        self.notebook = ttk.Notebook(self)
        self.int_tab = IntegrationTab(self.notebook)
        self.notebook.add(self.int_tab, text="Интегралы")
        self.notebook.pack(expand=True, fill="both")


if __name__ == "__main__":
    app = IntegralCalculatorApp()
    app.mainloop()