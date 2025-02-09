# -*- coding: utf-8 -*-

import os
import tkinter as tk
from tkinter import filedialog, messagebox
import requests
import base64
import pandas as pd

# 百度云应用的 API Key 和 Secret Key
API_KEY = "百度API_KEY"
SECRET_KEY = "百度SECRET_KEY"

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
    3. 提取返回结果中的“姓名”、“住址”、“公民身份号码”、“性别”
    返回一个字典，若出错则返回空字典
    """
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
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
    3. 提取返回结果中的“银行卡卡号”和“银行名称”
       如果银行卡卡号中存在空格，则去除空格
    返回一个字典，若出错则返回空字典
    """
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
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
    点击提取按钮后，进行 OCR 识别并生成 Excel 文件
    """
    if not selected_image_folder or not selected_output_folder:
        messagebox.showerror("错误", "请先选择图片文件夹和输出文件夹")
        return

    access_token = get_access_token()
    if not access_token:
        messagebox.showerror("错误", "获取 access token 失败")
        return

    # 获取文件夹中所有支持的图片文件
    valid_ext = {".jpg", ".jpeg", ".png", ".bmp"}
    files = [f for f in os.listdir(selected_image_folder) if os.path.splitext(f)[1].lower() in valid_ext]
    total_files = len(files)
    if total_files == 0:
        messagebox.showinfo("提示", "所选文件夹内没有可处理的图片")
        return

    results = []
    count = 0

    # 遍历文件夹中每个图片文件
    for filename in files:
        image_file = os.path.join(selected_image_folder, filename)
        # 分别调用身份证和银行卡识别接口
        id_data = process_idcard(image_file, access_token)
        bank_data = process_bankcard(image_file, access_token)
        # 合并两个结果字典；若识别不到，则对应字段为空
        combined = {
            "姓名": id_data.get("姓名", ""),
            "住址": id_data.get("住址", ""),
            "公民身份号码": id_data.get("公民身份号码", ""),
            "性别": id_data.get("性别", ""),
            "银行卡卡号": bank_data.get("银行卡卡号", ""),
            "银行名称": bank_data.get("银行名称", "")
        }
        results.append(combined)
        count += 1
        progress_label.config(text=f"已处理 {count} / {total_files} 个文件")
        root.update_idletasks()

    # 将所有结果写入 Excel 文件（第一行为列标题，后续每行对应一张图片的识别结果）
    if results:
        output_file = os.path.join(selected_output_folder, "ocr_result.xlsx")
        df = pd.DataFrame(results)
        df.to_excel(output_file, index=False)
        messagebox.showinfo("完成", f"已处理 {count} 个文件\nOCR 结果已保存到 {output_file}")
    else:
        messagebox.showwarning("提示", "没有成功处理的图片！")

def create_gui():
    """
    创建简单的 Tkinter GUI，包含按钮选择图片文件夹、输出文件夹，和提取按钮
    """
    global root, progress_label, image_folder_label, output_folder_label
    global selected_image_folder, selected_output_folder
    
    selected_image_folder = None
    selected_output_folder = None
    
    root = tk.Tk()
    root.title("身份证&银行卡批量识别")
    root.geometry("500x300")

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

    root.mainloop()

if __name__ == '__main__':
    create_gui()
