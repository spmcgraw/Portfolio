"""Import needed libraries"""
import random
import datetime
from os import system

# Constants and Global Variables
suits = ["Hearts", "Diamonds", "Spades", "Clubs"]
ranks = ["Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Jack",
        "Queen", "King", "Ace"]
rankValues = {
    "Two": 2, "Three": 3, "Four": 4, "Five": 5, "Six": 6, "Seven": 7, "Eight": 8,
    "Nine": 9, "Ten": 10, "Jack": 10, "Queen": 10, "King": 10, "Ace": 11
}

PLAYING = True

def print_divider():
    """Prints divider on terminal"""
    print("-----------------------------------------------------------")
    print("-----------------------------------------------------------")

def clear():
    """Clears the terminal"""
    clear_ = system('cls')
    return clear_

# 1. Create Card

class Card:
    """Build out the cards"""
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def __str__(self):
        return self.rank + " of " + self.suit

# 2. Create Deck and include a shuffle

class Deck:
    """Build out the deck using Card class"""
    def __init__(self):  # step through suits and ranks to create Card and Deck
        self.deck = []
        for suit in suits:
            for rank in ranks:
                self.deck.append(Card(suit, rank))

    def shuffle(self):
        """shuffles the deck"""
        random.shuffle(self.deck)

    def deal(self):
        """Deals the cards one at a time"""
        single_card = self.deck.pop(0)
        return single_card

# 3. Create Hand

class Hand:
    """Build out the hand"""
    def __init__(self):
        self.cards = []
        self.value = 0
        self.aces = 0

    def add_card(self, card):
        """Adds up the value of the cards"""
        self.cards.append(card)
        self.value += rankValues[card.rank]
        if card.rank == "Ace":
            self.aces += 1

    def adjust_aces(self):
        """checks if a card is an ace and makes it a 1 if over 21"""
        while self.value > 21 and self.aces:
            self.value -= 10
            self.aces -= 1

# 4. Create Player and Dearler Profiles with name, wallet, and hand
class Player:
    """Build out player profile"""
    def __init__(self, name, wallet = 100):
        self.name = name
        self.wallet = wallet
        self.bet = 0
        self.hand = Hand()

    def print_hand(self):
        """Prints player's hand"""
        print(f"\n{self.name}'s hand is: ", *self.hand.cards, sep = '\n')
        print(f"Card value = {self.hand.value}")

    def update_wallet(self, result):
        """Updates the player's wallet if they won"""
        if result == "won":
            self.wallet += self.bet
        else:
            self.wallet -= self.bet

class Dealer:
    """Build out dealer profile"""
    def __init__(self):
        self.hand = Hand()

    # Print dealer hand in stages
    def print_hand_stage1(self):
        """Prints dealer's hand"""
        print("\nDealer's hand is: ")
        print("<card hidden>")
        print(f" {self.hand.cards[1]}")

    def print_hand_all(self):
        """Show's dealer's hand and value"""
        print("\nDealer's hand is: ", *self.hand.cards, sep="\n")
        print("Dealer's hand =", self.hand.value)

# 5. Define functions used for game play
def take_bet(player):
    """Take bet from the player"""
    while True:
        try:
            player.bet = int(input("How much would you like to bet? "))
        except ValueError:
            print("Sorry, you bet must be an integer!")
        else:
            if player.bet > player.wallet:
                print(f"Sorry, your bet cannot exceed {player.wallet}")
            else:
                break

def hit(deck, hand):
    """If player hits take more cards"""
    hand.add_card(deck.deal())
    hand.adjust_aces()

def hit_or_stand(deck, hand):
    """Askes player if they want to hit or stand"""
    global PLAYING

    while True:
        h_or_s = input("Would you like to Hit or Stand? Enter 'h' or 's'")

        if h_or_s[0].lower() == 'h':
            hit(deck, hand)
        elif h_or_s[0].lower() == 's':
            print("Player stands. Dealer is playing.")
            PLAYING = False
        else:
            print("Sorry, please try again.")
            continue
        break

def player_busts(player):
    """What to do if player busts"""
    print("Player busts!")
    player.update_wallet("lost")

def player_wins(player):
    """What to do if player wins"""
    print(f"{player.name} wins!")
    player.update_wallet("won")

def dealer_busts(player):
    """What to do if dealer busts"""
    print("Dealer busts!")
    player.update_wallet("won")

def dealer_wins(player):
    """What to do if dealer wins"""
    print("Dealer wins!")
    player.update_wallet("lost")

def push(player):
    """What happens if it is a tie"""
    print(f"Dealer and {player.name} tie! It's a push.")

def greeting():
    """Creates a greeting"""
    date_time = str(datetime.datetime.now().time())
    date_time = int(date_time[:2])
    time_of_day = ""
    if date_time < 12 and date_time > 00:
        time_of_day = "Good morning!"
    elif date_time > 12 and date_time < 18:
        time_of_day = "Good afternoon!"
    else:
        time_of_day = "Good evening!"

    while True:
        try:
            name = input(f"{time_of_day} Please enter your name:\n")
            name = name[0].upper() + name[1:].lower()
            try:
                wallet = int(
                    input("How much money would you like to start with? (Default is $100)\n")
                    )
            except ValueError:
                wallet = 100
            break
        except IndexError:
            print("Enter a name first.")
            continue
    return name, wallet
# 6. Greet Player and ask for name
clear()
print_divider()
print("Welcome to Sean's Casino (BlackJack v1.0)")
print_divider()

playername, playerwallet = greeting()

# 7. Game play loop
while True:
    # Create & shuffle deck, deal two cards to each player
    deck = Deck()
    deck.shuffle()

    player1 = Player(playername, playerwallet)
    player1.hand.add_card(deck.deal())
    player1.hand.add_card(deck.deal())

    dealer = Dealer()
    dealer.hand.add_card(deck.deal())
    dealer.hand.add_card(deck.deal())

    # Prompt the Player for their bet
    take_bet(player1)

    # Show cards with keeping one dealer card hidden
    dealer.print_hand_stage1()
    player1.print_hand()

    while PLAYING:

        # Prompt to see if player wants to hit or stand
        hit_or_stand(deck, player1.hand)

        # Show cards after player stands, still hiding one dealer card
        dealer.print_hand_stage1()
        player1.print_hand()

        # Check if player busts and break while loop
        if player1.hand.value > 21:
            player_busts(player1)

            break

    # If player did not bust, play Dealer's hand (rule: Dealer stands at >= 17)
    if player1.hand.value <= 21:

        while dealer.hand.value < 17:
            hit(deck, dealer.hand)

        # Show all cards now
        dealer.print_hand_all()
        player1.print_hand()

        # Check to see who won
        if dealer.hand.value > 21:
            dealer_busts(player1)
        elif dealer.hand.value > player1.hand.value:
            dealer_wins(player1)
        elif dealer.hand.value < player1.hand.value:
            player_wins(player1)
        else:
            push(player1)

    # Let player know how much they won and rest bet to 0 for new game
    print(f"\n {player1.name}'s won ${player1.bet} and now has ${player1.wallet} in their wallet.")
    player1.bet = 0

    # Ask to play again
    if player1.wallet > 0:
        new_game = input("Would you like to play again? Enter 'y' or 'n'")
        if new_game[0].lower() == 'y':
            PLAYING = True
            continue
        else:
            print("Thanks for playing!")
            break
    else:
        print("You have no more money left. Thanks for playing! Goodbye")
        break

