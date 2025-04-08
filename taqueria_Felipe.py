BajaTaco = 4.25
Burrito = 7.50
Bowl = 8.5
Nachos = 11.50
Quesadilla = 8.50
SuperBurrito = 8.50
SuperQuesadilla = 9.50
Taco = 3.00
TortillaSalad = 8.00

Cuenta = 0

while True:
    print("¿Qué desea pedir?")
    print("1. Bajo Taco: 4.25$")
    print("2. Burrito: 7.50$")
    print("3. Bowl: 8.50$")
    print("4. Nachos: 11.50$")
    print("5. Quesadilla: 8.50$")
    print("6. Super Burrito: 8.50$")
    print("7. Super Quesadilla: 9.50$")
    print("8. Taco: 3.00$")
    print("9. Tortilla Salad: 8.00$")
    print("Cualquier otra tecla. Salir o pagar.")

    opcion = input("Seleccione un número del 1 al 9 acorde al producto que quiera o 10 para salir o pagar: ")

    if opcion == "1":
        Cuenta += BajaTaco
        print(f"La cuenta se le quedaría en {Cuenta:.2f}$")
    elif opcion == "2":
        Cuenta += Burrito
        print(f"La cuenta se le quedaría en {Cuenta:.2f}$")
    elif opcion == "3":
        Cuenta += Bowl
        print(f"La cuenta se le quedaría en {Cuenta:.2f}$")
    elif opcion == "4":
        Cuenta += Nachos
        print(f"La cuenta se le quedaría en {Cuenta:.2f}$")
    elif opcion == "5":
        Cuenta += Quesadilla
        print(f"La cuenta se le quedaría en {Cuenta:.2f}$")
    elif opcion == "6":
        Cuenta += SuperBurrito
        print(f"La cuenta se le quedaría en {Cuenta:.2f}$")
    elif opcion == "7":
        Cuenta += SuperQuesadilla
        print(f"La cuenta se le quedaría en {Cuenta:.2f}$")
    elif opcion == "8":
        Cuenta += Taco
        print(f"La cuenta se le quedaría en {Cuenta:.2f}$")
    elif opcion == "9":
        Cuenta += TortillaSalad
        print(f"La cuenta se le quedaría en {Cuenta:.2f}$")
    else:
        print(f"TOTAL A PAGAR: {Cuenta:.2f}$")
        break