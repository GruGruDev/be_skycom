from utils.enums import EnumBase


class SourceLead(EnumBase):
    LEAD = "lead"
    ORDER = "order"
    UPLOAD_FILE = "upload_file"
    OTHER = "other"


class CustomerGender(EnumBase):
    FEMALE = "female"
    MALE = "male"
    OTHER = "other"


class CustomerRank(EnumBase):
    SILVER = "sliver"  # Dưới 3 Triệu
    GOLD = "gold"  # 3 Triệu
    DIAMOND = "diamond"  # 10 Triệu
    VIP = "vip"  # Trên 15

    @classmethod
    def get_spent_range(cls, rank=None):
        """ranked if spent greater than or equal to range `value`"""
        range_rank = {
            cls.SILVER: 0,
            cls.GOLD: 3000000,
            cls.DIAMOND: 10000000,
            cls.VIP: 15000000,
        }
        if rank:
            return range_rank[rank]
        return range_rank

    # @classmethod
    # def get_rank_from_customer(cls, customers):
    #     customers.last_shipping_completed_date = (
    #         parse_datetime(customers.last_shipping_completed_date)
    #         if customers.last_shipping_completed_date is not None
    #         and isinstance(customers.last_shipping_completed_date, str)
    #         else customer.last_shipping_completed_date
    #     )
    #     if (
    #         customer.last_shipping_completed_date is None
    #         or timezone.now() - customer.last_shipping_completed_date > timedelta(days=365)
    #         or customer.birthday is None
    #     ):
    #         return None
    #     spent = customer.shipping_completed_spent
    #     if spent is None:
    #         return None
    #     if spent >= cls.get_spent_range(cls.VIP):
    #         return cls.VIP
    #     if spent >= cls.get_spent_range(cls.DIAMOND):
    #         return cls.DIAMOND
    #     if spent >= cls.get_spent_range(cls.GOLD):
    #         return cls.GOLD
    #     if spent > cls.get_spent_range(cls.SILVER):
    #         return cls.SILVER
    #     return None  # @classmethod
    # def get_rank_from_customer(cls, customer):
    #     customer.last_shipping_completed_date = (
    #         parse_datetime(customer.last_shipping_completed_date)
    #         if customer.last_shipping_completed_date is not None
    #         and isinstance(customer.last_shipping_completed_date, str)
    #         else customer.last_shipping_completed_date
    #     )
    #     if (
    #         customer.last_shipping_completed_date is None
    #         or timezone.now() - customer.last_shipping_completed_date > timedelta(days=365)
    #         or customer.birthday is None
    #     ):
    #         return None
    #     spent = customer.shipping_completed_spent
    #     if spent is None:
    #         return None
    #     if spent >= cls.get_spent_range(cls.VIP):
    #         return cls.VIP
    #     if spent >= cls.get_spent_range(cls.DIAMOND):
    #         return cls.DIAMOND
    #     if spent >= cls.get_spent_range(cls.GOLD):
    #         return cls.GOLD
    #     if spent > cls.get_spent_range(cls.SILVER):
    #         return cls.SILVER
    #     return None
