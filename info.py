import sys
import os
import ctypes

try:
    import wmi
    import psutil
except ImportError as e:
    print(f"[!] Ошибка: не установлена библиотека ({e.name}).")
    print("    Установите: pip install wmi pywin32 psutil")
    sys.exit(1)


def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def bytes_to_gb(value) -> float:
    try:
        return round(int(value) / (1024 ** 3), 2)
    except (TypeError, ValueError):
        return 0.0


def get_form_factor(code) -> str:
    if code == 12:
        return "SODIMM (Ноутбук)"
    if code == 8:
        return "DIMM (ПК/Сервер)"
    if code is None:
        return "Неизвестно (нет данных)"
    return f"Неизвестно (код {code})"


def main():
    if sys.platform != "win32":
        print("Эта программа работает только на Windows.")
        sys.exit(1)

    if not is_admin():
        print("[!] Внимание: запустите CMD от имени администратора.")
        print("    Без прав часть данных WMI может быть недоступна.\n")

    c = wmi.WMI()
    installed_bytes = 0
    used_slots = 0

    print("=" * 52)
    print(" ФИЗИЧЕСКИЕ МОДУЛИ ПАМЯТИ")
    print("=" * 52)

    try:
        modules = list(c.Win32_PhysicalMemory())
    except Exception as e:
        modules = []
        print(f"[!] Не удалось прочитать Win32_PhysicalMemory: {e}")

    if not modules:
        print("Модули не найдены (WMI не отдал данные).")
    else:
        for i, mem in enumerate(modules, 1):
            cap = mem.Capacity
            if cap is not None:
                installed_bytes += int(cap)

            speed = mem.ConfiguredClockSpeed or mem.Speed
            speed_str = f"{speed} MHz" if speed else "Неизвестно"

            manufacturer = (mem.Manufacturer or "").strip() or "Неизвестно"
            part = (mem.PartNumber or "").strip() or "Неизвестно"
            slot = mem.DeviceLocator or "Неизвестно"

            print(f"\nПланка #{i}")
            print(f"  Гнездо:         {slot}")
            print(f"  Производитель:  {manufacturer}")
            print(f"  Объём:          {bytes_to_gb(cap)} GB")
            print(f"  Скорость:       {speed_str}")
            print(f"  Форм-фактор:    {get_form_factor(mem.FormFactor)}")
            print(f"  Номер детали:   {part}")
            used_slots += 1

    print("\n" + "=" * 52)
    print(" СИСТЕМНАЯ ПАМЯТЬ (WINDOWS)")
    print("=" * 52)

    try:
        vm = psutil.virtual_memory()
        total_gb = vm.total / (1024 ** 3)
        avail_gb = vm.available / (1024 ** 3)
        used_gb = vm.used / (1024 ** 3)
        print(f"Всего видит ОС:    {total_gb:.2f} GB")
        print(f"Использовано:      {used_gb:.2f} GB ({vm.percent}%)")
        print(f"Доступно:          {avail_gb:.2f} GB")
    except Exception as e:
        print(f"[!] psutil не смог прочитать память: {e}")
        total_gb = 0.0

    if installed_bytes > 0 and total_gb > 0:
        installed_gb = installed_bytes / (1024 ** 3)
        reserved = installed_gb - total_gb
        if reserved < 0:
            reserved = 0.0
        print(f"\nУстановлено физически: {installed_gb:.2f} GB")
        print(f"Зарезервировано:       {reserved:.2f} GB")
        print("(разница между планками и тем, что видит Windows)")

    print("\n" + "=" * 52)
    print(" СЛОТЫ (ГНЁЗДА)")
    print("=" * 52)

    try:
        arrays = list(c.Win32_PhysicalMemoryArray())
        total_slots = 0
        for arr in arrays:
            md = arr.MemoryDevices
            if md is not None:
                total_slots += int(md)

        if total_slots == 0:
            print("Количество слотов неизвестно (WMI не отдал данные).")
        else:
            empty = total_slots - used_slots
            if empty < 0:
                empty = 0
            print(f"Всего слотов:   {total_slots}")
            print(f"Занято:         {used_slots}")
            print(f"Свободно:       {empty}")
    except Exception as e:
        print(f"[!] Не удалось получить данные о слотах: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nПрервано пользователем.")
    except Exception as exc:
        print(f"\n[!] Непредвиденная ошибка: {exc}")
    input("\nНажмите Enter для выхода...")
