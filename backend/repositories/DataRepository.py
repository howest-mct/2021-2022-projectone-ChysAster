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
    def random_activiteit_geel():
        sql = "SELECT Activiteit, aantalMinuten, idActiviteiten FROM Activiteiten where isWater = 0 and gespeeldGeel = 0 ORDER BY RAND() LIMIT 1"
        print("geel")
        return Database.get_one_row(sql)

    @staticmethod
    def random_activiteit_water_geel():
        sql = "SELECT Activiteit, aantalMinuten, idActiviteiten FROM Activiteiten WHERE gespeeldGeel = 0 ORDER BY RAND() LIMIT 1"
        print("geel water")
        return Database.get_one_row(sql)

    @staticmethod
    def random_activiteit():
        sql = "SELECT Activiteit, aantalMinuten, idActiviteiten FROM Activiteiten RAND() LIMIT 1"
        return Database.get_one_row(sql)

    @staticmethod
    def random_activiteit_blauw():
        sql = "SELECT Activiteit, aantalMinuten, idActiviteiten FROM Activiteiten where isWater = 0 and gespeeldBlauw = 0 ORDER BY RAND() LIMIT 1"
        print("blauw")
        return Database.get_one_row(sql)

    @staticmethod
    def random_activiteit_water_blauw():
        sql = "SELECT Activiteit, aantalMinuten, idActiviteiten FROM Activiteiten WHERE gespeeldBlauw = 0 ORDER BY RAND() LIMIT 1"
        print("blauw water")
        return Database.get_one_row(sql)

    @staticmethod
    def create_historiek(Device_idDevice, waarde):
        sql = "INSERT INTO Historiek(Device_idDevice, waarde) VALUES (%s,%s)"
        params = [Device_idDevice, waarde]
        return Database.execute_sql(sql, params)

    @staticmethod
    def get_historiek():
        sql = "select idHistoriek, naam, tijdstip, waarde from Historiek left join Device ON Historiek.Device_idDevice = Device.idDevice order by idHistoriek DESC limit 10"
        return Database.get_rows(sql)

    @staticmethod
    def create_activiteit(Activiteit, isWater, aantalMinuten):
        sql = "INSERT INTO Activiteiten(Activiteit, isWater, aantalMinuten) VALUES (%s, %s, %s)"
        params = [Activiteit, isWater, aantalMinuten]
        return Database.execute_sql(sql, params)

    @staticmethod
    def reset_geel():
        sql = "UPDATE Activiteiten SET gespeeldGeel = 0"
        return Database.execute_sql(sql)

    @staticmethod
    def reset_blauw():
        sql = "UPDATE Activiteiten SET gespeeldBlauw = 0"
        return Database.execute_sql(sql)

    @staticmethod
    def set_gespeeld_geel(idActiviteiten):
        sql = "UPDATE Activiteiten SET gespeeldGeel = 1 WHERE idActiviteiten = %s"
        params = [idActiviteiten]
        return Database.execute_sql(sql, params)

    @staticmethod
    def set_gespeeld_blauw(idActiviteiten):
        sql = "UPDATE Activiteiten SET gespeeldBlauw = 1 WHERE idActiviteiten = %s"
        params = [idActiviteiten]
        return Database.execute_sql(sql, params)

    @staticmethod
    def get_temp_grafiek():
        # sql = "select waarde, tijdstip from Historiek where idHistoriek mod 1 = 0 order by idHistoriek DESC limit 20;"
        sql = "SELECT waarde, tijdstip FROM(SELECT * FROM Historiek where idHistoriek mod 3=0 ORDER BY idHistoriek DESC LIMIT 20)Var1 ORDER BY idHistoriek ASC;"
        return Database.get_rows(sql)

    @staticmethod
    def get_teams():
        sql = "select waarde,tijdstip from Historiek left join Device ON Historiek.Device_idDevice = Device.idDevice where Historiek.Device_idDevice = 1 order by idHistoriek DESC limit 10"
        return Database.get_rows(sql)

    @staticmethod
    def get_gespeeld_geel():
        sql = "SELECT Activiteit from Activiteiten where gespeeldGeel = 1"
        return Database.get_rows(sql)

    @staticmethod
    def get_gespeeld_blauw():
        sql = "SELECT Activiteit from Activiteiten where gespeeldBlauw = 1"
        return Database.get_rows(sql)

    @staticmethod
    def get_gespeeld(gespeeld):
        if gespeeld == 'geel':
            sql = 'SELECT Activiteit from Activiteiten where gespeeldGeel = 1'
        elif gespeeld == 'blauw':
            sql = 'SELECT Activiteit from Activiteiten where gespeeldBlauw = 1'
        return Database.get_rows(sql)

    @staticmethod
    def get_aantal_blauw():
        sql = "SELECT count(*) as aantal FROM p1.Activiteiten where gespeeldBlauw = 1"
        return Database.get_rows(sql)

    @staticmethod
    def get_aantal_geel():
        sql = "SELECT count(*) as aantal FROM p1.Activiteiten where gespeeldGeel= 1"
        return Database.get_rows(sql)
