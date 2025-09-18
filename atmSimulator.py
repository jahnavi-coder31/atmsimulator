import sqlite3
from getpass import getpass
from datetime import datetime

# Connect to SQLite database
db = sqlite3.connect("atm_simulator.db")
cursor = db.cursor()

# Create tables
cursor.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        account_number INTEGER PRIMARY KEY,
        pin INTEGER,
        balance REAL
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_number INTEGER,
        type TEXT,
        amount REAL,
        timestamp TEXT
    )
""")
db.commit()

# ---------------- Core Functions ---------------- #

def account_exists(account_number):
    cursor.execute("SELECT 1 FROM accounts WHERE account_number=?", (account_number,))
    return cursor.fetchone() is not None

def create_account(account_number, pin, balance=0.0):
    if account_exists(account_number):
        print("Account already exists. Choose a different account number.")
        return
    cursor.execute("INSERT INTO accounts (account_number, pin, balance) VALUES (?, ?, ?)",
                   (account_number, pin, balance))
    db.commit()
    print("Account created successfully!")

def check_balance(account_number):
    cursor.execute("SELECT balance FROM accounts WHERE account_number=?", (account_number,))
    result = cursor.fetchone()
    return result[0] if result else None

def deposit(account_number, amount):
    if not account_exists(account_number):
        print("Deposit failed: Account does not exist.")
        return None
    if amount <= 0:
        print("Deposit must be greater than 0.")
        return None
    balance = check_balance(account_number)
    new_balance = balance + amount
    cursor.execute("UPDATE accounts SET balance=? WHERE account_number=?", (new_balance, account_number))
    cursor.execute("INSERT INTO transactions (account_number, type, amount, timestamp) VALUES (?, ?, ?, ?)",
                   (account_number, "Deposit", amount, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    return new_balance

def withdraw(account_number, amount):
    if not account_exists(account_number):
        print("Withdrawal failed: Account does not exist.")
        return None
    balance = check_balance(account_number)
    if balance is None or amount <= 0 or balance < amount:
        print("Insufficient funds or invalid amount.")
        return None
    new_balance = balance - amount
    cursor.execute("UPDATE accounts SET balance=? WHERE account_number=?", (new_balance, account_number))
    cursor.execute("INSERT INTO transactions (account_number, type, amount, timestamp) VALUES (?, ?, ?, ?)",
                   (account_number, "Withdrawal", amount, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    return new_balance

def transfer(sender_acc, receiver_acc, amount):
    if not account_exists(receiver_acc):
        print("Transfer failed: Receiver account does not exist.")
        return
    if withdraw(sender_acc, amount) is not None:
        deposit(receiver_acc, amount)
        print(f"Transferred ${amount:.2f} from {sender_acc} to {receiver_acc}.")

def show_transactions(account_number, limit=5):
    cursor.execute("SELECT type, amount, timestamp FROM transactions WHERE account_number=? ORDER BY id DESC LIMIT ?",
                   (account_number, limit))
    rows = cursor.fetchall()
    print("\nLast Transactions:")
    if rows:
        for row in rows:
            print(f"{row[2]} | {row[0]} | ${row[1]:.2f}")
    else:
        print("No transactions found.")

def close_account(account_number):
    if not account_exists(account_number):
        print("Cannot close: Account does not exist.")
        return
    cursor.execute("DELETE FROM accounts WHERE account_number=?", (account_number,))
    cursor.execute("DELETE FROM transactions WHERE account_number=?", (account_number,))
    db.commit()
    print("Account closed successfully.")

def change_pin(account_number, old_pin, new_pin):
    cursor.execute("SELECT pin FROM accounts WHERE account_number=?", (account_number,))
    record = cursor.fetchone()
    if record and record[0] == old_pin:
        cursor.execute("UPDATE accounts SET pin=? WHERE account_number=?", (new_pin, account_number))
        db.commit()
        print("PIN changed successfully!")
    else:
        print("Incorrect old PIN.")

def view_account_details(account_number):
    cursor.execute("SELECT account_number, balance FROM accounts WHERE account_number=?", (account_number,))
    record = cursor.fetchone()
    if record:
        print("\nAccount Details")
        print(f"Account Number: {record[0]}")
        print(f"Current Balance: ${record[1]:.2f}")
    else:
        print("Account not found.")

def add_interest(account_number, rate=2.0):
    balance = check_balance(account_number)
    if balance is None:
        print("Account not found.")
        return
    interest = balance * (rate / 100)
    new_balance = deposit(account_number, interest)
    print(f"Interest of ${interest:.2f} added. New Balance: ${new_balance:.2f}")

# ---------------- ATM Menu ---------------- #

def atm_simulator():
    while True:
        print("\nWelcome to the ATM Simulator!")
        print("1. Create New Account")
        print("2. Login")
        print("3. Exit Program")
        
        try:
            choice = int(input("Enter your choice (1-3): "))
        except ValueError:
            print("Invalid input.")
            continue

        if choice == 1:
            try:
                account_number = int(input("Enter a new account number: "))
                pin = int(getpass("Enter a PIN: "))
                create_account(account_number, pin, 0.0)
            except ValueError:
                print("Invalid account number or PIN.")

        elif choice == 2:
            try:
                account_number = int(input("Enter your account number: "))
                pin = int(getpass("Enter your PIN: "))
            except ValueError:
                print("Invalid input.")
                continue

            cursor.execute("SELECT * FROM accounts WHERE account_number=? AND pin=?", (account_number, pin))
            if cursor.fetchone():
                while True:
                    print("\nATM Menu:")
                    print("1. Check Balance")
                    print("2. Deposit Money")
                    print("3. Withdraw Money")
                    print("4. Transfer Money")
                    print("5. Mini Statement")
                    print("6. Close Account")
                    print("7. Change PIN")
                    print("8. View Account Details")
                    print("9. Add Interest")
                    print("10. Logout")
                    
                    try:
                        option = int(input("Enter your choice (1-10): "))
                    except ValueError:
                        print("Invalid input.")
                        continue

                    if option == 1:
                        balance = check_balance(account_number)
                        print(f"Current Balance: ${balance:.2f}")
                    elif option == 2:
                        try:
                            amount = float(input("Enter deposit amount: $"))
                            new_balance = deposit(account_number, amount)
                            if new_balance is not None:
                                print(f"New Balance: ${new_balance:.2f}")
                        except ValueError:
                            print("Invalid amount.")
                    elif option == 3:
                        try:
                            amount = float(input("Enter withdrawal amount: $"))
                            new_balance = withdraw(account_number, amount)
                            if new_balance is not None:
                                print(f"New Balance: ${new_balance:.2f}")
                        except ValueError:
                            print("Invalid amount.")
                    elif option == 4:
                        try:
                            receiver = int(input("Enter receiver account number: "))
                            amount = float(input("Enter transfer amount: $"))
                            transfer(account_number, receiver, amount)
                        except ValueError:
                            print("Invalid input.")
                    elif option == 5:
                        show_transactions(account_number)
                    elif option == 6:
                        confirm = input("Are you sure you want to close your account? (yes/no): ").lower()
                        if confirm == "yes":
                            close_account(account_number)
                            break
                    elif option == 7:
                        try:
                            old_pin = int(getpass("Enter your old PIN: "))
                            new_pin = int(getpass("Enter your new PIN: "))
                            change_pin(account_number, old_pin, new_pin)
                        except ValueError:
                            print("Invalid PIN format.")
                    elif option == 8:
                        view_account_details(account_number)
                    elif option == 9:
                        try:
                            rate = float(input("Enter interest rate (default 2%): ") or 2.0)
                            add_interest(account_number, rate)
                        except ValueError:
                            print("Invalid rate.")
                    elif option == 10:
                        print("Logged out successfully.")
                        break
                    else:
                        print("Invalid choice. Try again.")
            else:
                print("Invalid account number or PIN.")

        elif choice == 3:
            print("Exiting ATM Simulator. Goodbye!")
            break
        else:
            print("Invalid choice.")

# ---------------- Run Program ---------------- #
if __name__ == "__main__":
    atm_simulator()
    cursor.close()
    db.close()
