import aiohttp
import asyncio
import base64
import datetime
import os
import urllib3
import re
import sys
import requests

time_today = datetime.datetime.now().strftime('%Y-%m-%d')


async def check_directory(session, url):
    try:
        qheaders = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64)", "Connection": "close"}
        async with session.get('https://' + url, headers=qheaders) as response:
            if response.status == 200:
                print("[+]目录存在：" + url)
    except aiohttp.ClientError as e:
        print("[-]Error 扫描错误:", str(e))


async def main():
    # 域名获取
    domain = input("域名> ")

    if domain == "":
        print("[-]Error 域名不能为空!")
        return

    print(domain)
    lock_on = input("域名是否正确？(y/n) > ")

    if lock_on.lower() != 'y':
        return

    # key获取
    with open('key.txt', 'r', encoding='utf-8') as f:
        key_data = f.readline()

    # api搜索
    search_key_word = "domain.suffix=" + '"' + domain + '"'  # 奇安信搜索语法
    search_key_word = base64.urlsafe_b64encode(search_key_word.encode("utf-8"))  # 按照文档方式加密
    search_key_word = search_key_word.decode('utf8')  # 去除b'
    page = input("页数:")  # 获得页数，每页10个

    if page == "":
        print("[-]Error 页数不能为空!")
        return

    print("[+]Done 加密完成，正在搜索！")
    print("--------------------------")
    api = "https://hunter.qianxin.com/openApi/search?api-key=" + key_data + "&search=" + search_key_word + "&page=" + page + "&page_size=10" + "&is_web=3" + "&start_time=2021-01-01&end_time=" + time_today  # api接口域名
    async with aiohttp.ClientSession() as session:
        async with session.get(api) as response:
            raw_data = await response.json()

    if not raw_data['data']['arr']:
        print("Error 数据为空！")
        return

    print("[+]数据搜索完成！")
    print()

    # 美化数据
    for finish_data in raw_data['data']['arr']:
        print("[+]域名: " + finish_data['url'])
        print("[+]IP: " + finish_data['ip'])
        print("[+]端口: " + str(finish_data['port']))
        print("[+]备案公司: " + finish_data['company'])
        print("[+]备案号: " + finish_data['number'])
        print("[+]地址: " + finish_data['country'])
        print("[+]状态码: " + str(finish_data['status_code']))
        print()

    # 保存到文件中
    result = input("数据是否保存在txt文本中？[y/n] ")
    if result.lower() == "y":
        current_time = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
        file_name = f"result_hunter_{current_time}.txt"
        with open(file_name, 'w', encoding='utf-8') as file:
            for finish_data in raw_data['data']['arr']:
                file.write("[+]域名: " + finish_data['url'] + "\n")
                file.write("[+]IP: " + finish_data['ip'] + "\n")
                file.write("[+]端口: " + str(finish_data['port']) + "\n")
                file.write("[+]备案公司: " + finish_data['company'] + "\n")
                file.write("[+]备案号: " + finish_data['number'] + "\n")
                file.write("[+]地址: " + finish_data['country'] + "\n")
                file.write("[+]状态码: " + str(finish_data['status_code']) + "\n")
                file.write("\n")
        print("[+]数据已保存到文件：" + file_name)
        print()
    print("[+]DNS信息！")
    # NSLOOKUP
    # SOA记录
    print("--------------")
    SOA_raw_data = os.system("nslookup -ty=soa " + domain)  # SOA记录的IP
    SOA_raw_data = str(SOA_raw_data)
    print("SOA记录IP: " + SOA_raw_data)
    print()

    # MX记录
    print("--------------")
    MX_raw_data = os.system("nslookup -ty=MX " + domain)  # MX记录的IP
    MX_raw_data = str(MX_raw_data)
    print("MX记录信息: " + MX_raw_data)
    print()

    # NS记录
    print("--------------")
    NS_raw_data = os.system("nslookup -ty=NS " + domain)
    NS_raw_data = str(NS_raw_data)
    print("NS记录信息" + NS_raw_data)

    # whois
    print()
    print("--------------")
    # api拼接
    urllib3.disable_warnings()
    whois_api = "https://v.api.aa1.cn/api/whois/index.php?domain=" + domain
    # 请求api
    whois_response = requests.get(whois_api, verify=False)
    whois_raw_data = whois_response.text

    if whois_raw_data == "":
        print("数据为空！")
    else:
        email_pattern = r"Registrar Abuse Contact Email: (\S+)"
        updated_date_pattern = r"Updated Date: ([\d\-TZ:]+)"
        creation_date_pattern = r"Creation Date: ([\d\-TZ:]+)"

        email_match = re.search(email_pattern, whois_raw_data)
        updated_date_match = re.search(updated_date_pattern, whois_raw_data)
        creation_date_match = re.search(creation_date_pattern, whois_raw_data)

        if email_match:
            registrar_abuse_contact_email = email_match.group(1)
            print("注册机构Email:", registrar_abuse_contact_email)

        if updated_date_match:
            updated_date = updated_date_match.group(1)
            print("更新时间:", updated_date)

        if creation_date_match:
            creation_date = creation_date_match.group(1)
            print("创建时间:", creation_date)
    print()

    print("--------------")
    print("[+]目录扫描中，可能会出现误报！")
    # 目录扫描
    with open("fuzz.txt", "r") as file:
        async with aiohttp.ClientSession() as session:
            tasks = []
            for line in file:
                directory = line.strip()
                url = domain + "/" + directory
                task = asyncio.create_task(check_directory(session, url))
                tasks.append(task)
                await asyncio.sleep(0.1)  # 每次扫描时间间隔为0.1秒钟
            await asyncio.gather(*tasks)

    print()
    print("[+]Done 查询结束！")


asyncio.run(main())
