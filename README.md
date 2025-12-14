ddata文件夹包括两个文件夹：（1）test文件夹里测试数据及，即测试三个大语言模型性能的原始数据，共有200个药物描述文本和1条中药材配伍禁忌数据；（2）verification文件夹里是验证集，即人工标注三元组数据，共有200个药物描述文本和1条中药材配伍禁忌数据。
config.py是配置文件，主要配置大语言模型的API Keys、定义定义输入目录、输出目录、提示词文件的路径、请求方法（豆包、DeepSeek、千问）。
deepseek.py是调用DeepSeek大语言模型的API的Python代码。
doubao.py是调用豆包大语言模型的API的Python代码。
qianwen.py是调用千问大语言模型的API的Python代码。
eevaluate.py是根据精确度(Precision)、召回率(Recall)和F1分数(F1-score) 3个普遍使用的经典评价指标来衡量三个大语言模型命名实体识别与关系抽取的性能。
