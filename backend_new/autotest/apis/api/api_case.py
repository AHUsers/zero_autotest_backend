from fastapi import APIRouter

from autotest.celery_worker.tasks import async_run_testcase
from autotest.corelibs.http import partner_success
from autotest.schemas.api.api_case import ApiCaseQuery, ApiCaseIn, ApiCaseId, ApiCaseRun, ApiCaseIdsQuery
from autotest.services.api.api_case import ApiCaseService

router = APIRouter()


@router.post('/list', description="用例列表")
async def suites_list(params: ApiCaseQuery):
    data = await ApiCaseService.list(params)
    return partner_success(data)


@router.post('/getCaseByIds', description="根据ids获取用例列表")
async def suites_list(params: ApiCaseIdsQuery):
    data = await ApiCaseService.get_case_by_ids(params)
    return partner_success(data)


@router.post('/saveOrUpdate', description="更新保存用例")
async def save_or_update(params: ApiCaseIn):
    data = await ApiCaseService.save_or_update(params)
    return partner_success(data.get("id"))


@router.post('/runTestCase', description="运行用例")
async def run_testcase(params: ApiCaseId):
    async_run_testcase.delay(params.id)
    return partner_success(msg="用例异步运行， 请稍后再测试报告列表查看 😊")


@router.post('/debugTestCase', description="调试用例")
async def debug_testcase(params: ApiCaseRun):
    data = await ApiCaseService.debug_case(params)
    return partner_success(data)


@router.post('/deleted', description="删除用例")
async def deleted(params: ApiCaseId):
    result = await ApiCaseService.deleted(params)
    return partner_success(result)


@router.post('/getCaseInfo', description="用例信息")
async def case_info(params: ApiCaseId):
    data = await ApiCaseService.get_case_info(params)
    return partner_success(data)
