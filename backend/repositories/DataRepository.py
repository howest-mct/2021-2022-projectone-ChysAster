from .Database import Database


class DataRepository:
    @staticmethod
    def json_or_formdata(request):
        if request.content_type == 'application/json':
            gegevens = request.get_json()
        else:
            gegevens = request.form.to_dict()
        return gegevens

    @staticmethod
    def read_status_lampen():
        sql = "SELECT * from lampen"
        return Database.get_rows(sql)

    @staticmethod
    def read_status_lamp_by_id(id):
        sql = "SELECT * from lampen WHERE id = %s"
        params = [id]
        return Database.get_one_row(sql, params)

    @staticmethod
    def update_status_lamp(id, status):
        sql = "UPDATE lampen SET status = %s WHERE id = %s"
        params = [status, id]
        return Database.execute_sql(sql, params)

    @staticmethod
    def update_status_alle_lampen(status):
        sql = "UPDATE lampen SET status = %s"
        params = [status]
        return Database.execute_sql(sql, params)

    @staticmethod
    def random_activiteit():
        sql = "SELECT Activiteit FROM Activiteiten ORDER BY RAND() LIMIT 1"
        return Database.get_rows(sql)

    @staticmethod
    def create_historiek(Device_idDevice, waarde):
        sql = "INSERT INTO Historiek(Device_idDevice, waarde) VALUES (%s,%s)"
        params = [Device_idDevice, waarde]
        return Database.execute_sql(sql, params)

    @staticmethod
    def get_historiek():
        sql = "select idHistoriek, naam, tijdstip, waarde from Historiek left join Device ON Historiek.Device_idDevice = Device.idDevice order by idHistoriek DESC limit 10"
        return Database.get_rows(sql)
