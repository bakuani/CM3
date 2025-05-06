import tkinter as tk
from tkinter import ttk, messagebox
import math
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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


def adaptive_integration(f, a, b, tol, method, variant):
    n = 10
    I_prev = method(f, a, b, n, variant)
    while True:
        n *= 2
        I = method(f, a, b, n, variant)
        if abs(I - I_prev) < tol:
            return I, n
        I_prev = I
        if n > 1_000_000:
            raise ValueError("Не удалось достичь требуемой точности")

def handle_improper_integral(f, a, b, tol, method, variant="left"):
    if getattr(f, "__name__", "") == "f_inv" and a < 0 < b:
        delta = min(abs(a), b)
        if math.isclose(delta, abs(a), rel_tol=1e-9) and math.isclose(delta, b, rel_tol=1e-9):
            return 0.0, None
        if abs(a) < b:
            new_a, new_b = delta, b
        else:
            new_a, new_b = a, -delta
        I, n = adaptive_integration(f, new_a, new_b, tol, method, variant)
        if new_b < 0:
            I = -I
        return I, n
    return adaptive_integration(f, a, b, tol, method, variant)



def f_poly(x):
    return -x**3 - x**2 + x + 3

def f_sqrt(x):
    return 1/math.sqrt(x) if x > 0 else float('inf')

def f_one_minus_x(x):
    return 1/(1-x) if x != 1 else float('inf')

def f_inv(x):
    return float('inf') if x == 0 else 1/x

FUNCTIONS = [
    (f_poly,        "-x³ - x² + x + 3"),
    (f_inv,         "1/x (x=0 — разрыв)")
]

METHODS = [
    ("Прямоуг. (левые)",  IntegralMethods.rectangle, 'left'),
    ("Прямоуг. (правые)", IntegralMethods.rectangle, 'right'),
    ("Прямоуг. (средние)", IntegralMethods.rectangle, 'middle'),
    ("Трапеции",          IntegralMethods.trapezoid, None),
    ("Симпсон",           IntegralMethods.simpson,   None),
]



class IntegrationTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        ttk.Label(self, text="Функция:").grid(row=0, column=0, sticky="w")
        self.func_cb = ttk.Combobox(self, values=[d for _, d in FUNCTIONS], state="readonly")
        self.func_cb.current(0)
        self.func_cb.grid(row=0, column=1, sticky="ew")

        for label, row in [("a",1), ("b",2), ("ε",3)]:
            ttk.Label(self, text=label+":").grid(row=row, column=0, sticky="w")
            entry = ttk.Entry(self)
            entry.grid(row=row, column=1, sticky="ew")
            setattr(self, f"{label}_entry", entry)

        ttk.Label(self, text="Метод:").grid(row=4, column=0, sticky="w")
        self.method_cb = ttk.Combobox(self, values=[m[0] for m in METHODS], state="readonly")
        self.method_cb.current(2)
        self.method_cb.grid(row=4, column=1, sticky="ew")

        btn = ttk.Button(self, text="Вычислить", command=self._on_calc)
        btn.grid(row=5, column=0, columnspan=2, pady=5)

        self.result = tk.Text(self, height=6, width=40, state="disabled")
        self.result.grid(row=6, column=0, columnspan=2, pady=5)

        self.fig = Figure(figsize=(5,4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().grid(row=0, column=2, rowspan=7, padx=10, pady=5)

    def _on_calc(self):
        try:
            idx_f = self.func_cb.current()
            f, desc = FUNCTIONS[idx_f]
            a = float(self.a_entry.get().replace(',', '.'))
            b = float(self.b_entry.get().replace(',', '.'))
            tol = float(self.ε_entry.get().replace(',', '.'))

            idx_m = self.method_cb.current()
            _, method_fun, variant = METHODS[idx_m]

            I, n = handle_improper_integral(f, a, b, tol, method_fun, variant)

            self.result.config(state="normal")
            self.result.delete(1.0, tk.END)
            self.result.insert(tk.END, f"∫ f(x) dx ≈ {I:.8f}\n")
            self.result.insert(tk.END, f"ε = {tol}\n")
            self.result.insert(tk.END, f"n = {n}\n")
            self.result.config(state="disabled")

            # строим график, заменяя недопустимые значения на math.nan
            xs = [a + i*(b-a)/300 for i in range(301)]
            ys = []
            for x in xs:
                try:
                    y = f(x)
                    ys.append(y if math.isfinite(y) else math.nan)
                except Exception:
                    ys.append(math.nan)

            self.ax.clear()
            self.ax.plot(xs, ys, label=desc)
            self.ax.fill_between(xs, ys, alpha=0.3)
            self.ax.set_xlabel("x")
            self.ax.set_ylabel("f(x)")
            self.ax.set_title("График функции")
            self.ax.legend()
            self.ax.grid(True)
            self.canvas.draw()

        except Exception as e:
            messagebox.showerror("Ошибка", str(e))


class IntegralCalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Численное интегрирование (несобственные интегралы)")
        self.geometry("1000x600")
        notebook = ttk.Notebook(self)
        tab = IntegrationTab(notebook)
        notebook.add(tab, text="Интегралы")
        notebook.pack(expand=True, fill="both")


if __name__ == "__main__":
    app = IntegralCalculatorApp()
    app.mainloop()
