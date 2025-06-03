import mysql.connector, asyncio, csv, traceback
from googletrans import Translator
import pyinputplus as pyip


class Scenario:
    '''Class for scenario'''
    def __init__(self):
        '''Connect to the Nomad database'''
        with open('nomad_db.csv', 'r') as self.credentialfile:
            self.credentials = list(csv.reader(self.credentialfile))
            self.primary_app_db = mysql.connector.connect(
                host = self.credentials[1][0],
                user = self.credentials[2][0],
                password = self.credentials[3][0],
                database = self.credentials[0][0],
                buffered = True)
        
        self.cursor = self.primary_app_db.cursor()
        self.scnID = pyip.inputInt('Please select scenario to translate ' \
                                'by entering the corresponding ID:')
        self.cursor.execute('''SELECT language
                        FROM scenario
                        WHERE id = %s;''', (self.scnID,))
        
        try:
            self.oldLangID = self.cursor.fetchone()[0]
        except Exception as e:
            traceback.print_exc()
            self.primary_app_db.close()
            self.cursor.close()
            print(f"An error occurred: {e}")
        
        self.cursor.execute('''SELECT language_code
                        FROM language
                        WHERE id = %s;''', (self.oldLangID,))
        
        self.oldLangCode = self.cursor.fetchone()[0]

        self.cursor.execute('''SELECT *
                        FROM language;''')
        for row in self.cursor.fetchall():
            print(str(row).strip('()'))

        self.newLangID = pyip.inputInt('Please select a language to translate the ' \
                                 'scenario into by entering the corresponding ID:')
        self.cursor.execute('''SELECT language_code
                          FROM language
                          WHERE id = %s;''', (self.newLangID,))
        
        self.newLangCode = self.cursor.fetchone()[0]
        self.tenantID = pyip.inputInt('Please select tenant by entering the corresponding ID:')
        

    def __repr__(self):
        return f"Scenario(scnID={self.scnID}, oldLangID={self.oldLangID}, " \
               f"oldLangCode={self.oldLangCode}, newLangID={self.newLangID}, " \
               f"newLangCode={self.newLangCode}, tenantID={self.tenantID})"
                    

class ScenarioCloner(Scenario):
    '''Class for cloning scenarios'''
    def __init__(self):
        super().__init__()
        self.translator = Translator()


    def clone_scenario(self, cursor, scnID: int, newLangID: int, tenantID: int) -> int:
        data = cursor.callproc('scenario_clone', (scnID, newLangID, tenantID, '@scenario_new'))
        new_scnID = data[3]
        return new_scnID
    

    async def translate_table_scenario(self, cursor, new_scnID: int) -> None:
        try:
            cursor.execute('''SELECT scenario_name, scenario_description FROM scenario 
                        WHERE id = %s;''', (new_scnID,))
            scn_data = cursor.fetchone()
            if scn_data is None:
                print('No scenario found with the given ID.')
                return
            print(f'Original scenario name: {scn_data[0]}, description: {scn_data[1]}')
            translated_name = await (self.translator.translate(scn_data[0], src=self.oldLangCode, 
                                                        dest=self.newLangCode))
            translated_desc = await (self.translator.translate(scn_data[1], src=self.oldLangCode, 
                                                        dest=self.newLangCode))
            print(f'Translated scenario name: {translated_name.text}, description: {translated_desc.text}')

            cursor.execute('''UPDATE scenario
                            SET scenario_name = %s, scenario_description = %s
                            WHERE id = %s;''', (translated_name.text, 
                                                f'Original : {scn_data[1]} \n Translated : {translated_desc.text}', 
                                                new_scnID))
            print('Data from table "scenario" translated successfully.')

        except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()


    async def translate_table_scenario_point(self, cursor, new_scnID: int) -> list:
        try: 
            cursor.execute('''SELECT id, scenario_point_name, scenario_point_description
                              FROM scenario_point
                              WHERE scenario = %s;''', (new_scnID,))
            scn_point_data = cursor.fetchall()
            for row in scn_point_data:
                point_ids = []
                point_id = row[0]
                point_name = row[1]
                point_desc = row[2]
                print(f'Original scenario point ID: {point_id}, name: {point_name}, description: {point_desc}')
                translated_name = await (self.translator.translate(point_name, src=self.oldLangCode,
                                                                dest=self.newLangCode))
                print(f'Translated scenario point name: {translated_name.text}')
                cursor.execute('''UPDATE scenario_point
                                SET scenario_point_name = %s
                                WHERE id = %s;''', (f'Original : {point_name} \n Translated : {translated_name.text}', point_id))
                translated_desc = await (self.translator.translate(point_desc, src=self.oldLangCode, 
                                                            dest=self.newLangCode))
                print(f'Translated scenario point description: {translated_desc.text}')
                cursor.execute('''UPDATE scenario_point
                                SET scenario_point_description = %s
                                WHERE id = %s;''', (f'Original : {point_desc} \n Translated : {translated_desc.text}', point_id))
                point_ids.append(point_id)
            print('Data from table "scenario_point" translated successfully.')
            return point_ids

        except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()


    async def translate_table_scn_question(self, cursor,  point_ids: list) -> None:
        scn_question = []
        scn_question_ids = []
        try:
            for point_id in point_ids:
                cursor.execute('''SELECT id, explanation
                                  FROM scenario_question
                                  WHERE scenario_point = %s;''', (point_id,))
                scn_question_data = cursor.fetchall()
                for row in scn_question_data:
                    scn_question_ids.append(row[0])
                    scn_question.append(row[1])
                    print(f'Original scenario question ID: {row[0]}, explanation: {row[1]}')
                    translated_explanation = await (self.translator.translate(row[1], src=self.oldLangCode,
                                                                dest=self.newLangCode))
                    print(f'Translated scenario question explanation: {translated_explanation.text}')
                    cursor.execute('''UPDATE scenario_question
                                    SET explanation = %s
                                    WHERE id = %s;''', (f'Original : {row[1]} \n Translated : {translated_explanation.text}', row[0]))
            print('Data from table "scenario_question" translated successfully.')

        except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()


async def main():
    scn_cloner = ScenarioCloner()
    new_scnID = scn_cloner.clone_scenario(scn_cloner.cursor,
                            scn_cloner.scnID, scn_cloner.newLangID, 
                            scn_cloner.tenantID)
    await scn_cloner.translate_table_scenario(scn_cloner.cursor, new_scnID)
    scn_point_ids = await scn_cloner.translate_table_scenario_point(scn_cloner.cursor, new_scnID)
    await scn_cloner.translate_table_scn_question(scn_cloner.cursor, scn_point_ids)
    scn_cloner.primary_app_db.commit()
    print('Scenario cloned and translated.')
    scn_cloner.primary_app_db.close()
    scn_cloner.cursor.close()
    return


if __name__ == '__main__':
    asyncio.run(main())
