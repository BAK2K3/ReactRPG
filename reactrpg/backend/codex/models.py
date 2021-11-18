from random import randint
from django.db import models
from django.utils.translation import gettext_lazy as _
from .functions import rarity_recursive, stat_modifier


class CodexQuerySet(models.QuerySet):
    """
    Codex Query Set
    -----------
    Codex Query Set for all variants
    of queries and their associated business
    logic.
    custom_filter:
        Queries full Codex based on search and sort params.
    hero_select:
        Queries DB for heroes available to current user.
    get_random:
        Obtains a random entry from the DB based on user's
        level and premium status.
    """

    def custom_filter(self, search_params, sort_params):
        """
        Used for filtering the full codex for any search
        parameters or filters requested by the user.
        """
        return self.filter(**search_params).order_by(sort_params)

    def hero_select(self, paid):
        """
        Used for obtaining list of heroes available to given
        user. Creates default set of "False", and adds the current
        user's paid state (True/False). This allows the query to
        obtain any hero in the DB with values in the set (allowed_content).
        """
        allowed_content = {False}
        allowed_content.add(paid)
        return self.filter(type="Hero",
                           paid__in=allowed_content).order_by('pk')

    def get_random(self, codex_type, paid, level):
        """
        Used for obtaining a single random entry in the database.
        This obtains a queryset, filters by the required parameters,
        counts the length of the queryset, and chooses a random index
        from the queryset.
        This is used for random items and enemies.
        """
        allowed_content = {False}
        allowed_content.add(paid)
        query = self.filter(type=codex_type,
                            paid__in=allowed_content,
                            min_level__lte=level)
        last = query.count() - 1
        index = randint(0, last)  # nosec
        return query[index]


class CodexManager(models.Manager):
    """
    Codex Manager
    -----------
    Codex Manager for calling the custom
    Codex Query Sets.
    get_queryset:
        Overrides the default Mode Manager Get Queryset
        to utilise the CodexQueryset.
    filter_queryset:
        Calls the custom_filter Queryset.
    hero_select:
        Calls the hero_select Queryset.
    get_random:
        Calls the get_random Queryset.
    """

    def get_queryset(self):
        """
        Overrides the default Model Manager Get Queryset
        to utilise the CodexQueryset.
        """
        return CodexQuerySet(self.model, using=self._db)

    def filter_queryset(self, search_params, sort_params):
        """
        Calls the custom_filter Queryset.
        """
        return (
                self.get_queryset().custom_filter(search_params, sort_params)
        )

    def hero_select(self, paid):
        """
        Calls the hero_select Queryset.
        """
        return self.get_queryset().hero_select(paid)

    def get_random(self, codex_type, paid=False, level=1):
        """
        Calls the get_random Queryset.
        """
        return self.get_queryset().get_random(codex_type, paid, level)


class Codex(models.Model):
    """
    Codex Model
    -----------
    Model for all entries within the Codex.
    A model which is immutable to the user; each
    entry is designed to be generated and modified
    before being inserted into other relative databases.
    Admins have the capability of manipulating this database.
    Attributes:
    -----------
    name:
        Entry Name
    alpha_name:
        Organised Name
    type:
        Choice of Enemy, Weapon, or Hero
    base_hp:
        Base Hit Points of entry
    base_attack:
        Base Speed of entry
    base_defense:
        Base Defense of entry
    base_speed:
        Base Speed of entry
    image:
        Image name of entry
    paid:
        Bool to confirm whether premium entry
    min_level:
        User's minimum level threshold.
    Methods:
    --------
    new_weapon:
        Method for generating a new weapon.
    new_enemy:
        Method for generating a new enemy.
    """

    class Meta:
        verbose_name_plural = 'Codex'

    class TypeChoices(models.TextChoices):
        """Type Text Choices for model Type field"""
        ENEMY = 'Enemy', _('Enemy')
        WEAPON = 'Weapon', _('Weapon')
        HERO = 'Hero', _('Hero')

    name = models.CharField(max_length=100)
    alpha_name = models.CharField(max_length=100, null=True, blank=True)
    type = models.CharField(max_length=10, choices=TypeChoices.choices,
                            default=TypeChoices.ENEMY)
    base_hp = models.IntegerField(default=5)
    base_attack = models.IntegerField(default=5)
    base_defense = models.IntegerField(default=5)
    base_speed = models.IntegerField(default=5)
    image = models.ImageField(null=False, blank=False)
    paid = models.BooleanField(default=False)
    min_level = models.IntegerField(choices=[(i, i) for i in range(1, 6)],
                                    null=True, blank=True)
    objects = CodexManager()

    def __str__(self):
        return self.name

    @classmethod
    def new_weapon(cls, paid, level):
        """
        Method for generating a new weapon.
        Method takes in Paid Status and User Level.
        Level of the weapon is determined at random,
        along with the rarity of the weapon.
        The base stats of the weapon generated are then
        modified by a random amount, the limits of the
        multiplier are effected by the weapon's current
        level and rarity.
        The stat modifications are applied by a order of
        magnitude equivalent to the weapon's rarity.
        """
        # Obtain new weapon
        weapon = cls.objects.get_random("Weapon", paid, level)

        # Determine level and rarity
        if level > 1:
            weapon.level = randint(1, level)  # nosec
            weapon.rarity = rarity_recursive(weapon.level)
        else:
            weapon.level = 1
            weapon.rarity = 1

        rarity_list = ["Common", "Uncommon", "Rare", "Epic", "Mythic"]
        weapon.rarity_text = rarity_list[weapon.rarity-1]

        # Apply modification in order of magnitude (rarity)
        # Double underscore used in for loop to avoid unused variable
        for __ in range(weapon.rarity):

            # Modify stats based on level and rarity
            weapon.base_hp = stat_modifier(weapon.base_hp,
                                           weapon.level,
                                           weapon.rarity)
            weapon.base_attack = stat_modifier(weapon.base_attack,
                                               weapon.level,
                                               weapon.rarity)
            weapon.base_speed = stat_modifier(weapon.base_speed,
                                              weapon.level,
                                              weapon.rarity)
            weapon.base_defense = stat_modifier(weapon.base_defense,
                                                weapon.level,
                                                weapon.rarity)
        return weapon

    @classmethod
    def new_enemy(cls, paid, level):
        """
        Method for generating a new enemy.
        Method takes in Paid Status and User Level.
        Level of the Enemy is determined at random.
        The base stats of the enemy generated are modified
        n number of times, where n is the monster's level, based
        on the current monster's level.
        Enemy must be over level 1 for the modification to occur.
        """

        # Obtain new enemy
        enemy = cls.objects.get_random("Enemy", paid, level)
        # Determine level
        if level > 1:
            enemy.level = randint(1, level)  # nosec
            # Modify stats based on level (progressive)
            # Double underscore used in for loop to avoid unused variable
            for __ in range(enemy.level - 1):
                enemy.base_hp = stat_modifier(enemy.base_hp,
                                              enemy.level)
                enemy.base_attack = stat_modifier(enemy.base_attack,
                                                  enemy.level)
                enemy.base_speed = stat_modifier(enemy.base_speed,
                                                 enemy.level)
                enemy.base_defense = stat_modifier(enemy.base_defense,
                                                   enemy.level)
        else:
            enemy.level = 1
        return enemy
