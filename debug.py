from regearbot_package.api_calls import ReGearInfo, AlbionApi
from regearbot_package.mogodb_data_manager import MongoDataManager
from pprint import pprint


if __name__ == '__main__':
    mong = MongoDataManager()
    app = ReGearInfo(name="Yocttar")
    app.get_deaths_info()
    app.get_display_format()
    # pprint(app.victim_info_list[0])
    # pprint(app.display_list[0]['items_as_png'])

    # app.submit_regear_request(event_id='585424797')
    # mong.delete_multiple_objects_from_db()
    # print(len(mong.export_objects_to_csv()))
