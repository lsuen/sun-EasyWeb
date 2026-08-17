"""
通用测试用例 - 基于标准字段的数据驱动测试

作者：孙文龙 | 许可证：MIT
"""
import pytest
import allure
from core.engine import Engine
from tests.conftest import load_test_data, execute_test_case, assert_test_result


# 加载所有测试数据 (自动处理 _temp.json 过滤)
ALL_TEST_DATA = load_test_data()


@allure.epic("Easy-Web自动化测试平台")
@allure.feature("数据驱动测试引擎")
class TestAuto:
    """
    通用测试类
    根据 Excel/JSON 中的 type 字段自动路由到不同的执行逻辑
    """
    
    @pytest.mark.parametrize("data", ALL_TEST_DATA)
    @allure.story("{data[name]}")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("{data[name]}")
    def test_auto_execute(self, engine: Engine, data: dict, config: dict):
        """
        通用测试执行入口
        
        步骤:
        1. 打开页面
        2. 执行操作 (根据 type 路由)
        3. 验证结果 (根据 expected_type 路由)
        """
        import allure
        
        # 1. 打开页面
        with allure.step(f"打开页面: {data['url']}"):
            engine.open(data['url'])
        
        # 2. 执行操作
        with allure.step(f"执行操作 [{data['type']}]: {data['name']}"):
            execute_test_case(engine, data, config)
        
        # 3. 验证结果
        with allure.step(f"验证结果 [{data['expected_type']}]: {data['expected_value']}"):
            assert_test_result(engine, data)
        
        # 附加用例信息到报告
        allure.attach(data.get('description', ''), "用例描述", allure.attachment_type.TEXT)
        allure.attach(data.get('priority', 'P1'), "优先级", allure.attachment_type.TEXT)
