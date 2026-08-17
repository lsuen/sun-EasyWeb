"""
生成标准模板和测试数据文件
"""
import openpyxl
from openpyxl import Workbook
import json
import os


def create_standard_template():
    """创建标准字段模板"""
    wb = Workbook()
    ws = wb.active
    ws.title = "测试用例"
    
    # 标准字段
    headers = [
        'id', 'name', 'type', 'url', 'selector', 'value', 
        'expected_type', 'expected_value', 'priority', 'description'
    ]
    
    # 写入表头
    ws.append(headers)
    
    # 写入示例数据
    examples = [
        {
            'id': 'TC001',
            'name': '搜索Selenium',
            'type': 'search',
            'url': '${base_url}/',
            'selector': '#search-input',
            'value': 'selenium',
            'expected_type': 'title',
            'expected_value': '搜索',
            'priority': 'P0',
            'description': '验证首页搜索功能'
        },
        {
            'id': 'TC002',
            'name': '管理员登录',
            'type': 'login',
            'url': '${base_url}/login',
            'selector': '#username,#password,#login-btn',
            'value': 'admin,123456',
            'expected_type': 'text',
            'expected_value': 'admin',
            'priority': 'P0',
            'description': '验证管理员登录成功'
        },
        {
            'id': 'TC003',
            'name': '导航至登录页',
            'type': 'nav',
            'url': '${base_url}/',
            'selector': '#login-link',
            'value': '',
            'expected_type': 'url',
            'expected_value': '/login',
            'priority': 'P1',
            'description': '验证点击登录链接跳转'
        }
    ]
    
    for row in examples:
        ws.append([
            row['id'], row['name'], row['type'], row['url'],
            row['selector'], row['value'], row['expected_type'],
            row['expected_value'], row['priority'], row['description']
        ])
    
    # 调整列宽
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column].width = adjusted_width
    
    wb.save('data/standard_template.xlsx')
    print("标准模板已生成: data/standard_template.xlsx")


def create_test_data():
    """创建测试数据文件 (JSON 格式)"""
    test_data = [
        {
            "id": "TC001",
            "name": "搜索Selenium",
            "type": "search",
            "url": "${base_url}/",
            "selector": "#search-input",
            "value": "selenium",
            "expected_type": "title",
            "expected_value": "搜索",
            "priority": "P0",
            "description": "验证首页搜索Selenium功能"
        },
        {
            "id": "TC002",
            "name": "搜索Python",
            "type": "search",
            "url": "${base_url}/",
            "selector": "#search-input",
            "value": "python",
            "expected_type": "title",
            "expected_value": "搜索",
            "priority": "P0",
            "description": "验证首页搜索Python功能"
        },
        {
            "id": "TC003",
            "name": "管理员登录",
            "type": "login",
            "url": "${base_url}/login",
            "selector": "#username,#password,#login-btn",
            "value": "admin,123456",
            "expected_type": "text",
            "expected_value": "admin",
            "priority": "P0",
            "description": "验证管理员登录成功"
        },
        {
            "id": "TC004",
            "name": "测试用户登录",
            "type": "login",
            "url": "${base_url}/login",
            "selector": "#username,#password,#login-btn",
            "value": "test,test123",
            "expected_type": "text",
            "expected_value": "test",
            "priority": "P0",
            "description": "验证测试用户登录成功"
        },
        {
            "id": "TC005",
            "name": "登录失败-错误密码",
            "type": "login",
            "url": "${base_url}/login",
            "selector": "#username,#password,#login-btn",
            "value": "admin,wrong",
            "expected_type": "text",
            "expected_value": "用户名或密码错误",
            "priority": "P1",
            "description": "验证错误密码登录失败"
        },
        {
            "id": "TC006",
            "name": "导航至登录页",
            "type": "nav",
            "url": "${base_url}/",
            "selector": "#login-link",
            "value": "",
            "expected_type": "url",
            "expected_value": "/login",
            "priority": "P1",
            "description": "验证点击登录链接跳转"
        },
        {
            "id": "TC007",
            "name": "导航至元素定位页",
            "type": "nav",
            "url": "${base_url}/",
            "selector": "#elements-link",
            "value": "",
            "expected_type": "url",
            "expected_value": "/elements",
            "priority": "P1",
            "description": "验证点击元素定位链接跳转"
        }
    ]
    
    with open('data/test_data.json', 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=4)
    
    print(f"测试数据已生成: data/test_data.json ({len(test_data)} 条)")


if __name__ == '__main__':
    create_standard_template()
    create_test_data()
    print("\n所有数据文件已生成！")
