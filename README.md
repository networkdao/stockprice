goldpricesend_v1.1主要功能：
1. 获取黄金的价格（通过 https://www.nowapi.com/api ）
2. 把获取的价格相关的信息存储到本地 csv 文件中
3. 当价格满足条件时发送短信（通过阿里云的短信平台）
4. 在结合  crontab 定时任务就可以控制程序运行的频率
   
