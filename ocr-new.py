import sys
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import requests
import base64
from PIL import Image
import io
import threading
from queue import Queue
from tkinter import ttk
import csv

# 百度云应用的 API Key 和 Secret Key
API_KEY = "百度API_KEY"
SECRET_KEY = "百度SECRET_KEY"

# 在全局变量部分添加
task_queue = Queue()
running_thread = None

def get_access_token():
    """
    使用 API_KEY 和 SECRET_KEY 获取 access token
    """
    token_url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", 
              "client_id": API_KEY, 
              "client_secret": SECRET_KEY}
    response = requests.post(token_url, params=params)
    result = response.json()
    return result.get("access_token")

def process_idcard(image_path, access_token):
    """
    处理身份证 OCR：
    1. 读取图片并转换为 Base64 编码字符串  
    2. 调用身份证 OCR 接口  
    3. 提取返回结果中的"姓名"、"住址"、"公民身份号码"、"性别"
    返回一个字典，若出错则返回空字典
    """
    try:
        # 读取图片并转换为webp格式
        with Image.open(image_path) as img:
            # 转换图片模式为RGB（兼容RGBA格式图片）
            if img.mode in ('RGBA', 'LA'):
                img = img.convert('RGB')
            
            # 使用BytesIO临时保存转换后的图片
            with io.BytesIO() as output:
                img.save(output, format="WEBP", quality=80, method=6)
                image_data = output.getvalue()
                
    except Exception as e:
        print(f"读取文件失败（身份证）：{image_path}，错误：{e}")
        return {}
    
    image_base64 = base64.b64encode(image_data).decode()
    request_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/idcard?access_token=" + access_token

    params = {
        "id_card_side": "front",  # 若识别反面，可改为 "back"
        "image": image_base64,
        "detect_direction": "true",
        "detect_photo": "false",
        "detect_quality": "false",
        "detect_risk": "false",
        "detect_ps": "false",
        "detect_card": "false"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    try:
        response = requests.post(request_url, data=params, headers=headers)
        result = response.json()
        print(f"身份证 OCR 返回结果（{os.path.basename(image_path)}）：")
        print(result)
        words_result = result.get("words_result", {})
        data = {
            "姓名": words_result.get("姓名", {}).get("words", ""),
            "住址": words_result.get("住址", {}).get("words", ""),
            "公民身份号码": words_result.get("公民身份号码", {}).get("words", ""),
            "性别": words_result.get("性别", {}).get("words", "")
        }
        return data
    except Exception as e:
        print(f"处理身份证失败（{image_path}）：{e}")
        return {}

def process_bankcard(image_path, access_token):
    """
    处理银行卡 OCR：
    1. 读取图片并转换为 Base64 编码字符串  
    2. 调用银行卡 OCR 接口  
    3. 提取返回结果中的"银行卡卡号"和"银行名称"
       如果银行卡卡号中存在空格，则去除空格
    返回一个字典，若出错则返回空字典
    """
    try:
        # 读取图片并转换为webp格式
        with Image.open(image_path) as img:
            # 转换图片模式为RGB
            if img.mode in ('RGBA', 'LA'):
                img = img.convert('RGB')
            
            with io.BytesIO() as output:
                img.save(output, format="WEBP", quality=80, method=6)
                image_data = output.getvalue()
                
    except Exception as e:
        print(f"读取文件失败（银行卡）：{image_path}，错误：{e}")
        return {}
    
    image_base64 = base64.b64encode(image_data).decode()
    request_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/bankcard?access_token=" + access_token

    # 注意：银行卡 OCR 也需要传入 image 参数
    params = {
        "image": image_base64,
        "location": "false",
        "detect_quality": "false"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    try:
        response = requests.post(request_url, data=params, headers=headers)
        result = response.json()
        print(f"银行卡 OCR 返回结果（{os.path.basename(image_path)}）：")
        print(result)
        # 获取银行卡卡号，并去掉空格
        bank_card_number = result.get("result", {}).get("bank_card_number", "")
        bank_card_number = bank_card_number.replace(" ", "")
        bank_data = {
            "银行卡卡号": bank_card_number,
            "银行名称": result.get("result", {}).get("bank_name", "")
        }
        return bank_data
    except Exception as e:
        print(f"处理银行卡失败（{image_path}）：{e}")
        return {}

def select_image_folder():
    """
    弹出文件夹选择对话框，选择包含图片的文件夹
    """
    folder_path = filedialog.askdirectory(title="选择图片文件夹")
    if not folder_path:
        return
    
    image_folder_label.config(text=f"选择的图片文件夹：{folder_path}")
    global selected_image_folder
    selected_image_folder = folder_path

def select_output_folder():
    """
    弹出文件夹选择对话框，选择输出 Excel 文件的文件夹
    """
    output_folder = filedialog.askdirectory(title="选择输出文件夹")
    if not output_folder:
        return
    
    output_folder_label.config(text=f"选择的输出文件夹：{output_folder}")
    global selected_output_folder
    selected_output_folder = output_folder

def process_images():
    """ 
    新版本：将耗时代码移入线程
    """
    def worker():
        try:
            access_token = get_access_token()
            if not access_token:
                task_queue.put(("error", "获取 access token 失败"))
                return

            valid_ext = {".jpg", ".jpeg", ".png", ".bmp"}
            files = [f for f in os.listdir(selected_image_folder) if os.path.splitext(f)[1].lower() in valid_ext]
            total_files = len(files)
            
            if total_files == 0:
                task_queue.put(("info", "所选文件夹内没有可处理的图片"))
                return

            results = []
            for i, filename in enumerate(files):
                image_file = os.path.join(selected_image_folder, filename)
                id_data = process_idcard(image_file, access_token)
                bank_data = process_bankcard(image_file, access_token)
                
                combined = {
                    "姓名": id_data.get("姓名", ""),
                    "住址": id_data.get("住址", ""),
                    "公民身份号码": id_data.get("公民身份号码", ""),
                    "性别": id_data.get("性别", ""),
                    "银行卡卡号": bank_data.get("银行卡卡号", ""),
                    "银行名称": bank_data.get("银行名称", "")
                }
                results.append(combined)
                
                # 通过队列发送进度更新
                task_queue.put(("progress", i+1, total_files))

            if results:
                output_file = os.path.join(selected_output_folder, f"识别结果.csv")
                try:
                    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
                        writer = csv.writer(f)
                        # 写入标题行
                        headers = ["姓名", "性别", "住址", "公民身份号码", "银行卡卡号", "银行名称"]
                        writer.writerow(headers)
                        
                        # 写入数据行
                        for row in results:
                            data = [
                                row["姓名"],
                                row["性别"],
                                row["住址"],
                                f"'{row['公民身份号码']}",  # 添加单引号强制文本格式
                                f"'{row['银行卡卡号']}",    # 添加单引号强制文本格式
                                row["银行名称"]
                            ]
                            writer.writerow(data)
                    task_queue.put(("complete", f"已处理 {len(files)} 个文件\n结果保存到 {output_file}"))
                except Exception as e:
                    task_queue.put(("error", f"保存文件失败：{str(e)}"))
            else:
                task_queue.put(("warning", "没有成功处理的图片！"))

        except Exception as e:
            task_queue.put(("error", f"处理过程中发生错误：{str(e)}"))

    def update_gui():
        while not task_queue.empty():
            task_type, *args = task_queue.get()
            if task_type == "progress":
                current, total = args
                progress = int((current / total) * 100)
                progress_label.config(text=f"已处理 {current} / {total} 个文件")
                progress_bar["value"] = progress
            elif task_type == "complete":
                messagebox.showinfo("完成", args[0])
                extract_btn.config(state="normal")
                progress_bar["value"] = 0
            elif task_type == "error":
                messagebox.showerror("错误", args[0])
                extract_btn.config(state="normal")
                progress_bar["value"] = 0
            elif task_type == "info":
                messagebox.showinfo("提示", args[0])
            elif task_type == "warning":
                messagebox.showwarning("警告", args[0])
        
        if running_thread.is_alive():
            root.after(100, update_gui)

    # 禁用按钮并启动线程
    extract_btn.config(state="disabled")
    progress_bar["value"] = 0
    thread = threading.Thread(target=worker)
    global running_thread
    running_thread = thread
    thread.start()
    root.after(100, update_gui)

def create_gui():
    """
    创建简单的 Tkinter GUI，包含按钮选择图片文件夹、输出文件夹，和提取按钮
    """
    global root, progress_label, image_folder_label, output_folder_label, progress_bar, extract_btn
    global selected_image_folder, selected_output_folder
    
    selected_image_folder = None
    selected_output_folder = None
    
    root = tk.Tk()
    root.title("身份证&银行卡批量识别")
    root.geometry("500x320")  # 微调高度适应进度条

    # 选择图片文件夹按钮
    select_image_folder_btn = tk.Button(root, text="选择图片文件夹", command=select_image_folder, font=("宋体", 14))
    select_image_folder_btn.pack(pady=10)
    
    image_folder_label = tk.Label(root, text="选择的图片文件夹：", font=("宋体", 12))
    image_folder_label.pack(pady=5)

    # 选择输出文件夹按钮
    select_output_folder_btn = tk.Button(root, text="选择输出文件夹", command=select_output_folder, font=("宋体", 14))
    select_output_folder_btn.pack(pady=10)
    
    output_folder_label = tk.Label(root, text="选择的输出文件夹：", font=("宋体", 12))
    output_folder_label.pack(pady=5)

    # 提取按钮
    extract_btn = tk.Button(root, text="提取", command=process_images, font=("宋体", 14))
    extract_btn.pack(pady=20)

    progress_label = tk.Label(root, text="等待处理...", font=("宋体", 12))
    progress_label.pack(pady=10)

    # 添加进度条
    progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
    progress_bar.pack(pady=5)

    root.mainloop()

if __name__ == '__main__':
    create_gui()
