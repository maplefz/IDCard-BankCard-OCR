# IDCard-BankCard-OCR

使用[百度智能云图片识别API](https://ai.baidu.com/tech/ocr)  识别身份证和银行卡，并导出指定字段至excel文件，带一个简单的GUI。
填入申请的API_KEY和SECRET_KEY，个人认证 1,000 次/月，企业认证 2,000 次/月。[收费标准：](https://ai.baidu.com/ai-doc/OCR/9k3h7xuv6)  

- 需要的依赖
``pip install requests pandas openpyxl``
- 编译exe
编译设置软件图标  
``pyinstaller --onefile --windowed --icon=your_icon.ico your_script.py``
编译不想显示控制台窗口
``pyinstaller --onefile --windowed --noconsole your_script.py``
