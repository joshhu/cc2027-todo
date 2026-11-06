from datetime import date

WEEKDAYS = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


def main():
    today = date.today()
    print(f"今天是 {today.year} 年 {today.month} 月 {today.day} 日，{WEEKDAYS[today.weekday()]}")


if __name__ == "__main__":
    main()
