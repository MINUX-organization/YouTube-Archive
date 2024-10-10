import blockcypher
from moneywagon import AddressBalance

def balance(addr):
    try:
        total = blockcypher.get_total_balance(addr)
        print('Balance is '+ str(total / 10^7))
    except:
        total = AddressBalance().action('btc', addr)
        print('Balance is '+ str(total))


def main():
	addr = input("Enter an Address :>  ")
	balance(addr)

if __name__ == '__main__':
	main()
