from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image


class ImageProcessorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PNG 背景抠图工具")
        self.root.geometry("760x680")
        self.root.minsize(700, 620)

        self.input_dir_var = tk.StringVar()
        self.output_dir_var = tk.StringVar()

        self.bg_r_var = tk.IntVar(value=255)
        self.bg_g_var = tk.IntVar(value=0)
        self.bg_b_var = tk.IntVar(value=255)

        self.remove_tolerance_var = tk.IntVar(value=80)
        self.despill_strength_var = tk.DoubleVar(value=1.0)

        self.build_ui()

    def build_ui(self):
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        # ===== 路径区 =====
        path_frame = ttk.LabelFrame(main, text="目录设置", padding=10)
        path_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(path_frame, text="输入目录：").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(path_frame, textvariable=self.input_dir_var, width=70).grid(row=0, column=1, padx=6, pady=4, sticky="ew")
        ttk.Button(path_frame, text="选择...", command=self.choose_input_dir).grid(row=0, column=2, pady=4)

        ttk.Label(path_frame, text="输出目录：").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(path_frame, textvariable=self.output_dir_var, width=70).grid(row=1, column=1, padx=6, pady=4, sticky="ew")
        ttk.Button(path_frame, text="选择...", command=self.choose_output_dir).grid(row=1, column=2, pady=4)

        path_frame.columnconfigure(1, weight=1)

        # ===== 参数区 =====
        param_frame = ttk.LabelFrame(main, text="参数设置", padding=10)
        param_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(param_frame, text="背景色 R：").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Spinbox(param_frame, from_=0, to=255, textvariable=self.bg_r_var, width=8).grid(row=0, column=1, sticky="w", pady=4)

        ttk.Label(param_frame, text="G：").grid(row=0, column=2, sticky="w", pady=4)
        ttk.Spinbox(param_frame, from_=0, to=255, textvariable=self.bg_g_var, width=8).grid(row=0, column=3, sticky="w", pady=4)

        ttk.Label(param_frame, text="B：").grid(row=0, column=4, sticky="w", pady=4)
        ttk.Spinbox(param_frame, from_=0, to=255, textvariable=self.bg_b_var, width=8).grid(row=0, column=5, sticky="w", pady=4)

        ttk.Label(param_frame, text="删背景容差：").grid(row=1, column=0, sticky="w", pady=8)
        ttk.Scale(
            param_frame,
            from_=0,
            to=150,
            variable=self.remove_tolerance_var,
            orient="horizontal",
            length=260
        ).grid(row=1, column=1, columnspan=4, sticky="w")
        self.remove_tol_label = ttk.Label(param_frame, text=str(self.remove_tolerance_var.get()))
        self.remove_tol_label.grid(row=1, column=5, sticky="w")

        ttk.Label(param_frame, text="去边缘残色强度：").grid(row=2, column=0, sticky="w", pady=8)
        ttk.Scale(
            param_frame,
            from_=0.0,
            to=2.0,
            variable=self.despill_strength_var,
            orient="horizontal",
            length=260
        ).grid(row=2, column=1, columnspan=4, sticky="w")
        self.despill_label = ttk.Label(param_frame, text=f"{self.despill_strength_var.get():.2f}")
        self.despill_label.grid(row=2, column=5, sticky="w")

        self.remove_tolerance_var.trace_add("write", self.update_labels)
        self.despill_strength_var.trace_add("write", self.update_labels)

        # ===== 说明区 =====
        help_frame = ttk.LabelFrame(main, text="参数说明", padding=10)
        help_frame.pack(fill="x", pady=(0, 10))

        help_text = (
            "1. 背景色 RGB：要移除的背景参考颜色。默认值为 (255, 0, 255)。\n"
            "2. 背景匹配容差：越大，越容易把接近背景色的像素变为透明；过大可能影响主体边缘。\n"
            "   - 建议范围：60 ~ 100\n"
            "3. 边缘去残色强度：用于减轻主体边缘残留的背景染色或杂色。\n"
            "   - 建议范围：0.7 ~ 1.2\n"
            "4. 本工具只处理 PNG 文件，输出格式仍为 PNG。\n"
            "5. 如果背景去除不彻底，可适当提高背景匹配容差；如果主体边缘发灰或失真，可适当降低边缘去残色强度。"
        )
        ttk.Label(help_frame, text=help_text, justify="left").pack(anchor="w")

        # ===== 操作区 =====
        action_frame = ttk.Frame(main)
        action_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(action_frame, text="开始处理", command=self.process_images).pack(side="left")
        ttk.Button(action_frame, text="清空日志", command=self.clear_log).pack(side="left", padx=8)

        self.progress_var = tk.StringVar(value="等待开始")
        ttk.Label(action_frame, textvariable=self.progress_var).pack(side="right")

        # ===== 日志区 =====
        log_frame = ttk.LabelFrame(main, text="处理日志", padding=10)
        log_frame.pack(fill="both", expand=True)

        self.log_text = tk.Text(log_frame, height=18, wrap="word")
        self.log_text.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)

    def update_labels(self, *args):
        self.remove_tol_label.config(text=str(self.remove_tolerance_var.get()))
        self.despill_label.config(text=f"{self.despill_strength_var.get():.2f}")

    def choose_input_dir(self):
        folder = filedialog.askdirectory(title="选择输入目录")
        if folder:
            self.input_dir_var.set(folder)

    def choose_output_dir(self):
        folder = filedialog.askdirectory(title="选择输出目录")
        if folder:
            self.output_dir_var.set(folder)

    def log(self, text: str):
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
        self.root.update_idletasks()

    def clear_log(self):
        self.log_text.delete("1.0", "end")

    @staticmethod
    def is_bg_like(r, g, b, bg_r, bg_g, bg_b, tolerance):
        return (
            abs(r - bg_r) <= tolerance and
            abs(g - bg_g) <= tolerance and
            abs(b - bg_b) <= tolerance
        )

    @staticmethod
    def has_transparent_neighbor(px, x, y, w, h):
        for ny in range(max(0, y - 1), min(h, y + 2)):
            for nx in range(max(0, x - 1), min(w, x + 2)):
                if nx == x and ny == y:
                    continue
                if px[nx, ny][3] == 0:
                    return True
        return False

    def process_one_image(self, img: Image.Image) -> Image.Image:
        bg_r = self.bg_r_var.get()
        bg_g = self.bg_g_var.get()
        bg_b = self.bg_b_var.get()
        remove_tolerance = self.remove_tolerance_var.get()
        despill_strength = self.despill_strength_var.get()

        img = img.convert("RGBA")
        px = img.load()
        w, h = img.size

        # 第一遍：删背景
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if a > 0 and self.is_bg_like(r, g, b, bg_r, bg_g, bg_b, remove_tolerance):
                    px[x, y] = (0, 0, 0, 0)

        # 第二遍：边缘去残色
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if a == 0:
                    continue

                if self.has_transparent_neighbor(px, x, y, w, h):
                    magenta_excess = min(r, b) - g
                    if magenta_excess > 0:
                        reduce_amount = int(magenta_excess * despill_strength)

                        r = max(0, r - reduce_amount)
                        b = max(0, b - reduce_amount)
                        g = min(255, g + reduce_amount // 2)

                        px[x, y] = (r, g, b, a)

        return img

    def process_images(self):
        input_dir = Path(self.input_dir_var.get().strip())
        output_dir = Path(self.output_dir_var.get().strip())

        if not input_dir.exists() or not input_dir.is_dir():
            messagebox.showerror("错误", "输入目录无效。")
            return

        if not self.output_dir_var.get().strip():
            messagebox.showerror("错误", "请先选择输出目录。")
            return

        output_dir.mkdir(parents=True, exist_ok=True)

        files = sorted(input_dir.glob("*.png"))
        if not files:
            messagebox.showwarning("提示", "输入目录中没有找到 PNG 文件。")
            return

        self.log("开始处理...")
        self.log(f"输入目录: {input_dir}")
        self.log(f"输出目录: {output_dir}")
        self.log(
            f"参数: BG=({self.bg_r_var.get()}, {self.bg_g_var.get()}, {self.bg_b_var.get()}), "
            f"容差={self.remove_tolerance_var.get()}, 去边缘残色强度={self.despill_strength_var.get():.2f}"
        )
        self.log("-" * 60)

        success_count = 0

        for index, file in enumerate(files, start=1):
            try:
                with Image.open(file) as img:
                    result = self.process_one_image(img)
                    save_path = output_dir / file.name
                    result.save(save_path)

                success_count += 1
                self.progress_var.set(f"处理中: {index}/{len(files)}")
                self.log(f"[OK] {file.name}")
            except Exception as e:
                self.log(f"[ERR] {file.name}: {e}")

        self.progress_var.set(f"完成: {success_count}/{len(files)}")
        self.log("-" * 60)
        self.log(f"处理完成，成功 {success_count} / {len(files)}")
        messagebox.showinfo("完成", f"处理完成。\n成功: {success_count} / {len(files)}")


def main():
    root = tk.Tk()
    try:
        root.iconbitmap("")
    except Exception:
        pass
    app = ImageProcessorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()