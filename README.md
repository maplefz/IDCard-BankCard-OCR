# IDCard-BankCard-OCR

使用[百度智能云图片识别API](https://ai.baidu.com/tech/ocr)  识别身份证和银行卡，并导出指定字段至excel文件，带一个简单的GUI。
填入申请的API_KEY和SECRET_KEY。免费额度：个人认证 1,000 次/月，企业认证 2,000 次/月。[收费标准：](https://ai.baidu.com/ai-doc/OCR/9k3h7xuv6)  
需要将身份证正面和银行卡带卡号面合并在一张图片中  

- 需要的依赖  
```python
pip install requests pandas openpyxl
```
- 编译exe  
编译设置软件图标
```cmd
pyinstaller --onefile --windowed --icon=your_icon.ico your_script.py
```
编译不想显示控制台窗口  
```cmd
pyinstaller --onefile --windowed --noconsole your_script.py
```

软件界面：   
<img src="https://raw.githubusercontent.com/maplefz/IDCard-BankCard-OCR/refs/heads/main/assets/1-main.jpg" width="300px">

图片样例：  
<img src="https://raw.githubusercontent.com/maplefz/IDCard-BankCard-OCR/refs/heads/main/assets/2-sample.jpg" width="300px">

输出的excel文件内容样例：  
![excel样例](https://raw.githubusercontent.com/maplefz/IDCard-BankCard-OCR/refs/heads/main/assets/3-result.jpg)  

### 更新日志
- ocr-new
去除pandas和openpyxl的依赖，直接导出csv文件，并且将“身份证号码”、“银行卡卡号”增加前引号以避免数字被科学计数处理。去除依赖后可以减小编译后的体积。使用目录模式编译能加快软件的打开速度。  
使用PowerShell编译例子
```PowerShell
py -3.13 -m PyInstaller -D -w `
--add-data "$(& py -3.13 -c 'import PIL; print(PIL.__path__[0])');PIL" `
--exclude-module numpy `
--exclude-module tkinter `
your.py
```

- 后记
另外亦可以使用[腾讯云API](https://cloud.tencent.com/document/product/866/33524),免费额度为1000次/月。但是API调用方法和返回的内容均和百度不一样，需要对应修改。
