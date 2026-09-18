import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.geometry("400x250")
app.title("Моё приложение")

def on_click():
    label.configure(text="Кнопка нажата!")

label = ctk.CTkLabel(app, text="Привет, мир!", font=("Arial", 18))
label.pack(pady=20)

btn = ctk.CTkButton(app, text="Нажми меня", command=on_click)
btn.pack(pady=10)

app.mainloop()