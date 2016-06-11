from itertools import groupby

class HandEvaluator:

  HIGHCARD      = 0
  ONEPAIR       = 1 << 8
  TWOPAIR       = 1 << 9
  THREECARD     = 1 << 10
  STRAIGHT      = 1 << 11
  FLASH         = 1 << 12
  FULLHOUSE     = 1 << 13
  FOURCARD      = 1 << 14
  STRAIGHTFLASH = 1 << 15

  # Return Format
  # [Bit flg of hand][rank1(4bit)][rank2(4bit)]
  # ex.)
  #       HighCard hole card 3,4   =>           100 0011
  #       OnePair of rank 3        =>        1 0011 0000
  #       TwoPair of rank A, 4     =>       10 1110 0100
  #       ThreeCard of rank 9      =>      100 1001 0000
  #       Straight of rank 10      =>     1000 1010 0000
  #       Flash of rank 5          =>    10000 0101 0000
  #       FullHouse of rank 3, 4   =>   100000 0011 0100
  #       FourCard of rank 2       =>  1000000 0010 0000
  #       straight flash of rank 7 => 10000000 0111 0000
  @classmethod
  def eval_hand(self, hole, community):
    cards = hole + community
    if self.__is_straightflash(cards): return self.STRAIGHTFLASH | self.__eval_straightflash(cards)
    if self.__is_fullhouse(cards): return self.FULLHOUSE | self.__eval_fullhouse(cards)
    if self.__is_flash(cards): return self.FLASH | self.__eval_flash(cards)
    if self.__is_straight(cards): return self.STRAIGHT | self.__eval_straight(cards)
    if self.__is_threecard(cards): return self.THREECARD | self.__eval_threecard(cards)
    if self.__is_twopair(cards): return self.TWOPAIR | self.__eval_twopair(cards)
    if self.__is_onepair(cards): return self.ONEPAIR | (self.__eval_onepair(cards) << 4)
    return self.__eval_holecard(hole)

  @classmethod
  def __eval_holecard(self, hole):
    ranks = sorted([card.rank for card in hole])
    return ranks[1] << 4 | ranks[0]

  @classmethod
  def __is_onepair(self, cards):
    return self.__eval_onepair(cards) != -1

  @classmethod
  def __eval_onepair(self, cards):
    rank = -1
    memo = 0  # bit memo
    for card in cards:
      mask = 1 << card.rank
      if memo & mask != 0: rank = max(rank, card.rank)
      memo |= mask
    return rank

  @classmethod
  def __is_twopair(self, cards):
    return len(self.__search_twopair(cards)) == 2

  @classmethod
  def __eval_twopair(self, cards):
    ranks = self.__search_twopair(cards)
    return ranks[1] << 4 | ranks[0]

  @classmethod
  def __search_twopair(self, cards):
    ranks = []
    memo = 0
    for card in cards:
      mask = 1 << card.rank
      if memo & mask != 0: ranks.append(card.rank)
      memo |= mask
    return sorted(ranks)[:2]

  @classmethod
  def __is_threecard(self, cards):
    return self.__search_threecard(cards) != -1

  @classmethod
  def __eval_threecard(self, cards):
    return self.__search_threecard(cards) << 4

  @classmethod
  def __search_threecard(self, cards):
    rank = -1
    bit_memo = reduce(lambda memo,card: memo + (1 << (card.rank-1)*3), cards, 0)
    for r in range(2, 15):
      bit_memo >>= 3
      count = bit_memo & 7
      if count >= 3: rank = r
    return rank

  @classmethod
  def __is_straight(self, cards):
    return self.__search_straight(cards) != -1

  @classmethod
  def __eval_straight(self, cards):
    return self.__search_straight(cards) << 4

  @classmethod
  def __search_straight(self, cards):
    bit_memo = reduce(lambda memo, card: memo | 1 << card.rank, cards, 0)
    rank = -1
    straight_check = lambda acc, i: acc & (bit_memo >> (r+i) & 1) == 1
    for r in range(2, 15):
      if reduce(straight_check, range(5), True): rank = r
    return rank

  @classmethod
  def __is_flash(self, cards):
    return self.__search_flash(cards) != -1

  @classmethod
  def __eval_flash(self, cards):
    return self.__search_flash(cards) << 4

  @classmethod
  def __search_flash(self, cards):
    best_suit_rank = -1
    fetch_suit = lambda card: card.suit
    fetch_rank = lambda card: card.rank
    for suit, group_obj in groupby(sorted(cards, key=fetch_suit), key=fetch_suit):
      g = list(group_obj)
      if len(g) >= 5:
        max_rank_card = max(g, key=fetch_rank)
        best_suit_rank = max(best_suit_rank, max_rank_card.rank)
    return best_suit_rank

  @classmethod
  def __is_fullhouse(self, cards):
    r1, r2 = self.__search_fullhouse(cards)
    return r1 and r2

  @classmethod
  def __eval_fullhouse(self, cards):
    r1, r2 = self.__search_fullhouse(cards)
    return r1 << 4 | r2

  @classmethod
  def __search_fullhouse(self, cards):
    fetch_rank = lambda card: card.rank
    three_card_ranks, two_pair_ranks = [], []
    for rank, group_obj in groupby(sorted(cards, key=fetch_rank), key=fetch_rank):
      g = list(group_obj)
      if len(g) >= 3:
        three_card_ranks.append(rank)
      if len(g) >= 2:
        two_pair_ranks.append(rank)
    two_pair_ranks = [rank for rank in two_pair_ranks if not rank in three_card_ranks]
    if len(three_card_ranks) == 2:
      two_pair_ranks.append(min(three_card_ranks))
    max_ = lambda l: None if len(l)==0 else max(l)
    return max_(three_card_ranks), max_(two_pair_ranks)

  @classmethod
  def __is_straightflash(self, cards):
    return self.__search_straightflash(cards) != -1

  @classmethod
  def __eval_straightflash(self, cards):
    return self.__search_straightflash(cards) << 4

  @classmethod
  def __search_straightflash(self, cards):
    flash_cards = []
    fetch_suit = lambda card: card.suit
    for suit, group_obj in groupby(sorted(cards, key=fetch_suit), key=fetch_suit):
      g = list(group_obj)
      if len(g) >= 5: flash_cards = g
    return self.__search_straight(flash_cards)

  @classmethod
  def __mask_strength(self, bit):
    return bit & (511 << 8)  # 511 = (1 << 9) -1

  @classmethod
  def __high_rank(self, bit):
    mask = 15 << 4
    return (bit & 240) >> 4

  @classmethod
  def __low_rank(self, bit):
    mask = 15
    return bit & mask

