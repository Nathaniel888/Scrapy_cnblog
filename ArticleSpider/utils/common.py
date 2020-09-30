import hashlib

def get_md5(url):
    #判断传入的是不是一个字符串，是的话使用utf-8编码
    if isinstance(url,str):
        url = url.encode("utf-8")

    m = hashlib.md5()
    m.update(url)

    return m.hexdigest()



if __name__ == "__main__":
    print(get_md5('https://news.cnblogs.com/n/674004/'))