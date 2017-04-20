README
=======

这是个基于web.py和sqlite的短链服务，为了编码方便还使用了peewee。（python2.7）

使用方法
-------
安装依赖
```bash
pip install -r requirements
```

修改代码11行的host和12行的port
```python
host = "10.67.13.145"
port = 8080
```

跑起来：
```bash
python main.py
```