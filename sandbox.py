import datetime

# time = datetime.datetime.now()

first_date = "30/11/2020"
second_date = "30/11/2020 17:30:00"
formatted_date1 = datetime.datetime.strptime(first_date, "%d/%m/%Y")

print(formatted_date1.day)
# formatted_date1 = datetime.datetime.strptime(first_date, "%d/%m/%Y %H:%M:%S")
# formatted_date2 = datetime.datetime.strptime(second_date, "%d/%m/%Y %H:%M:%S")
# print(datetime.datetime.strptime("30/11/2020", "%d/%m/%Y") in first_date)