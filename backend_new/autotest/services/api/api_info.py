import typing

from autotest.exceptions import ParameterError
from autotest.models.api_models import ApiInfo
from autotest.schemas.api.api_info import ApiQuery, ApiId, ApiInfoIn, ApiInfoRun, ApiRunSchema
from autotest.schemas.api.test_report import TestReportSaveSchema
from autotest.services.api.run_handle import ApiInfoHandle
from autotest.services.api.test_report import ReportService
from zerorunner.testcase import ZeroRunner
from autotest.utils.serialize import default_serialize


class ApiInfoService:
    @staticmethod
    async def list(params: ApiQuery) -> typing.Dict:
        """
        接口列表
        :param params:
        :return:
        """
        data = await ApiInfo.get_list(params)
        return data

    @staticmethod
    async def save_or_update(params: ApiInfoIn) -> typing.Dict:
        """
        更新保存测试用例/配置
        :param params:
        :return:
        """
        if not params.name:
            raise ParameterError("用例名不能为空!")
        # 判断用例名是否重复
        if params.id:
            api_info = await ApiInfo.get(params.id)
            if not api_info:
                raise ParameterError("用例不存在!")
            if api_info.name != params.name:
                if ApiInfo.get_api_by_name(name=params.name):
                    raise ParameterError("用例名重复!")

        return await ApiInfo.create_or_update(params.dict())

    @staticmethod
    def set_api_status(**kwargs: typing.Any):
        """
        用例失效生效
        :param kwargs:
        :return:
        """
        ids = kwargs.get('ids', None)
        case_list = ApiInfo.get_list(ids=ids).all()
        for case_info in case_list:
            case_info.case_status = 20 if case_info.case_status == 10 else 10
            case_info.save()

    @staticmethod
    def deleted(c_id: typing.Union[int, str]):
        """
        删除测试用例
        :param c_id:
        :return:
        """
        case_info = ApiInfo.get(c_id)
        case_info.delete() if case_info else ...

    @staticmethod
    async def detail(params: ApiId) -> typing.Dict:
        """
        获取用例信息
        :param params:
        :return:
        """
        case_info = await ApiInfo.get_api_by_id(params.id)
        if not case_info:
            raise ValueError('当前用例不存在！')

        return case_info

    @staticmethod
    async def run(params: ApiRunSchema):
        """
        运行测试用例
        :param params:
        :return:
        """
        case_info = await ApiInfo.get(params.id)
        run_params = ApiInfoRun(**default_serialize(case_info), env_id=params.env_id)
        case_info = await ApiInfoHandle.init(run_params)
        await case_info.make_functions()

        runner = ZeroRunner()
        summary = runner.run_tests(case_info.get_testcase())
        report_params = TestReportSaveSchema(
            name=summary.name,
            start_time=summary.start_time,
            duration=summary.duration,
            case_id=summary.case_id,
            run_mode="case",
            run_type=10,
            success=summary.success,
            run_count=summary.run_count,
            actual_run_count=summary.actual_run_count,
            run_success_count=summary.run_success_count,
            run_fail_count=summary.run_fail_count,
            run_skip_count=summary.run_skip_count,
            run_err_count=summary.run_err_count,
            run_log=summary.log,
            project_id=case_info.api_info.project_id,
            module_id=case_info.api_info.module_id,
            env_id=case_info.api_info.env_id
        )
        report_info = await ReportService.save_report(report_params)

        await ReportService.save_report_detail(summary, report_info.get('id', None))

        return report_info

    @staticmethod
    async def debug_api(params: ApiInfoRun) -> typing.Any:
        """
        用例调试
        :param params:
        :return:
        """
        case_info = await ApiInfoHandle.init(params)
        await case_info.make_functions()
        runner = ZeroRunner()
        summary = runner.run_tests(case_info.get_testcase())
        return summary

    @staticmethod
    def postman2api(json_body: typing.Dict, **kwargs):
        """postman 转 api"""
        coll = Collection(json_body)
        coll.make_test_case()
        for testcase in coll.case_list:
            case = {
                "name": testcase.name,
                "priority": 3,
                "code": kwargs.get('code', ''),
                "project_id": kwargs.get('project_id', None),
                "module_id": kwargs.get('module_id', None),
                "service_name": kwargs.get('service_name', ''),
                "config_id": kwargs.get('config_id', None),
                "user_id": get_user_id_by_token(),
                "testcase": testcase.dict(),
            }
            parsed_data = ApiInfoIn(**case).dict()
            case_info = ApiInfo()
            case_info.update(**parsed_data)
        return len(coll.case_list)
