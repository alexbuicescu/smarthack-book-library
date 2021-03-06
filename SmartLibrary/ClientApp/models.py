#!/usr/bin/env python
from datetime import datetime, timedelta
from django.db import models
from django.contrib.auth.models import User
from itertools import chain
from django.db.models.signals import post_save
from django.core.validators import MaxValueValidator, MinValueValidator
import numpy as np

from passlib.hash import bcrypt


# from .charting import compute_coords

join_querysets = lambda sets: set(chain(*sets))
GRADE_VALIDATORS = [MinValueValidator(1), MaxValueValidator(10)]


class Book(models.Model):
    title = models.CharField(max_length=256, blank=False, null=False)
    short_name = models.CharField(max_length=16)
    author = models.CharField(max_length=512)
    description = models.CharField(max_length=2048)
    release_date = models.DateField()
    cover_url = models.CharField(max_length=512)

    # Features for clustering
    complexity = models.IntegerField(validators=GRADE_VALIDATORS)
    nr_pages =   models.IntegerField(validators=GRADE_VALIDATORS)
    popularity = models.IntegerField(validators=GRADE_VALIDATORS)
    humor =      models.IntegerField(validators=GRADE_VALIDATORS)
    featureX =   models.IntegerField(validators=GRADE_VALIDATORS)
    featureY =   models.IntegerField(validators=GRADE_VALIDATORS)

    GENRES = [
        ('SF', 'Sci-Fi'),
        ('Fan', 'Fantasy'),
        ('Prog', 'Programming'),
        ('SelfDev', 'Self Development'),
        ('R', 'Romance'),
    ]
    genre = models.CharField(choices=GENRES, max_length=16)

    def __str__(self):
        return self.title

    def loaners(self):
        loans = Loan.objects.filter(book=self)
        return [loan.user for loan in loans]

    def loaned_together(self):
        loans = Loan.objects.filter(book=self)
        loans_around = [loan.user.profile.loaned_around(loan.start_date) for loan in loans]
        return join_querysets(loans_around) - {self}

    def nearest(self, coords, n_neighbours=2):
        self_coords = coords[coords.book == self.short_name]

        x = self_coords.x2D.values[0]
        y = self_coords.y2D.values[0]
        cluster = self_coords.cluster2D.values[0]

        coords = coords[coords.cluster2D == cluster]  # only look in the same cluster
        coords['distance'] = np.sqrt((coords.x2D - x) ** 2 + (coords.y2D - y) ** 2)  # euclidian distance
        coords = coords.sort_values(by='distance')
        coords = coords.ix[1:1+n_neighbours]  # first one (index 0) is itself
        book_names = coords.book

        return Book.objects.filter(short_name__in=book_names)


class Loan(models.Model):
    user = models.ForeignKey(User, related_name='loans')
    book = models.ForeignKey(Book)
    start_date = models.DateTimeField(default=datetime.now)
    return_date = models.DateTimeField(default=lambda: datetime.now() + timedelta(days=30))

    def __str__(self):
        return '%s - %s' % (self.user, self.book)


class Profile(models.Model):
    # access like: request.user.profile.google_id
    user = models.OneToOneField(User)
    google_id = models.CharField(max_length=64)
    hashed_password = models.CharField(max_length=512)

    def loaned_around(self, date):
        before = date - timedelta(minutes=10)
        after  = date + timedelta(minutes=10)
        loans = self.user.loans.filter(start_date__range=[before, after])
        return [loan.book for loan in loans]


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


post_save.connect(create_user_profile, sender=User)


def populate():
    def make(model, **kwargs):
        obj, created = model.objects.get_or_create(**kwargs)
        obj.save()
        return obj

    # Books
    lotr = make(Book,
                title='Lord of the Rings',
                short_name='LotR',
                author='JRR Tolkein',
                description='Book with dwarfs and elves',
                release_date=datetime(day=24, month=1, year=1994),
                cover_url='https://images.gr-assets.com/books/1411114164l/33.jpg',
                genre='Fan',

                complexity=6,
                nr_pages=400,
                popularity=8,
                humor=5,

                featureX=2,
                featureY=10
                )

    sw = make(Book,
              title='Star Wars',
              short_name='SW',
              author='George Lucas',
              description='Here is the untold story of the events that took place between the movies The Empire Strikes Back and Return of the Jedi: a novel in which Darth Vader still lives--and battles a villain as powerful and evil as himself.',
              release_date=datetime(day=31, month=8, year=1994),
              cover_url='https://images.gr-assets.com/books/1360058156l/359805.jpg',
              genre='SF',

              complexity=3,
              nr_pages=500,
              popularity=9,
              humor=3,

                featureX=1,
                featureY=10
              )

    cormen = make(Book,
                  title='Algorithms 3rd Edition',
                  short_name='Cormen',
                  author='Cormen et al',
                  description='Data structures and algorithms -- good book',
                  release_date=datetime(day=1, month=5, year=2000),
                  cover_url='https://images.gr-assets.com/books/1387741681l/108986.jpg',
                  genre='Prog',

                  complexity=8,
                  nr_pages=800,
                  popularity=6,
                  humor=1,

                featureX=9,
                featureY=8
                  )

    got = make(Book,
               title='Game of Thrones',
               short_name='GoT',
               author='George RR Martin',
               description='Sex and slayings',
               release_date=datetime(day=5, month=6, year=2013),
               cover_url='https://images.gr-assets.com/books/1369052110l/12962439.jpg',
               genre='Fan',

               complexity=3,
               nr_pages=300,
               popularity=8,
               humor=2,

                featureX=3,
                featureY=4
               )

    mindfulness = make(Book,
               title='Mindfulness for Beginners',
               short_name='Mindfulness',
               author='Jon Kabat-Zinn',
               description='What if you could profoundly change your life just by becoming more mindful of your breathing? According to Jon Kabat-Zinn, you can. What if paying attention on purpose (and nonjudgmentally) could improve your health? Again, according to Dr. Kabat-Zinn it can.',
               release_date=datetime(day=5, month=6, year=2006),
               cover_url='https://images.gr-assets.com/books/1446584518l/14098.jpg',
               genre='SelfDev',

               complexity=3,
               nr_pages=2,
               popularity=3,
               humor=1,

                featureX=9,
                featureY=2
               )

    meditation = make(Book,
               title='Meditation: Achieving Inner Peace and Tranquility In Your Life',
               short_name='Meditation',
               author='Brian L. Weiss',
               description='Meditation is a technique that can be used to experience peace, tranquility, and an inner beauty, leading us to rethink everything around us, even ourselves. It prompts us to trust in the ability we have to use and direct our energies to purify our bodies and minds...so that we can discover and develop our spirituality.',
               release_date=datetime(day=5, month=6, year=2002),
               cover_url='https://images.gr-assets.com/books/1348999317l/167603.jpg',
               genre='SelfDev',

               complexity=4,
               nr_pages=64,
               popularity=3,
               humor=1,

                featureX=10,
                featureY=1

               )

    nonrunner = make(Book,
               title='The Non-Runner\'s Marathon Trainer',
               short_name='Non-Runner',
               author='David A. Whitsett',
               description='Athlete. Runner. Marathoner. Are these words you wouldn\'t exactly use to describe yourself? Do you consider yourself too old or too out of shape to run a marathon? But somewhere deep inside have you always admired the people who could reach down and come up with the mental and physical strength to complete such a daunting and rewarding accomplishment?',
               release_date=datetime(day=5, month=6, year=1998),
               cover_url='https://images.gr-assets.com/books/1296236131l/98248.jpg',
               genre='SelfDev',

               complexity=4,
               nr_pages=288,
               popularity=3,
               humor=1,

                featureX=10,
                featureY=2
               )

    performance = make(Book,
               title='Spartan Up!: A take-no-prisoners guide to overcoming obstacles and achieving peak preformance in life',
               short_name='Spartan Up!',
               author='Joe De Sena',
               description='De Sena\’s prescription for life’s insurmountable obstacles is to get off the couch and crush them through hard work and force of will. A legend in the ultramarathon community, he created Spartan Race, extreme obstacle races where no one knows what to expect, but to finish is to be transformed.',
               release_date=datetime(day=5, month=6, year=2014),
               cover_url='https://images.gr-assets.com/books/1393362571l/19583491.jpg',
               genre='SelfDev',

               complexity=4,
               nr_pages=224,
               popularity=3,
               humor=1,

                featureX=10,
                featureY=3
               )

    prince = make(Book,
               title='The Little Prince',
               short_name='Prince',
               author='Antonie de Saint-Exupery',
               description='With a timeless charm it tells the story of a little boy who leaves the safety of his own tiny planet to travel the universe, learning the vagaries of adult behaviour through a series of extraordinary encounters. His personal odyssey culminates in a voyage to Earth and further adventures. ',
               release_date=datetime(day=5, month=6, year=1943),
               cover_url='https://images.gr-assets.com/books/1367545443l/157993.jpg',
               genre='Fan',

               complexity=1,
               nr_pages=83,
               popularity=8,
               humor=3,
               
                featureX=5,
                featureY=10

               )


    notebook = make(Book,
               title='The Notebook',
               short_name='Notebook',
               author='Nicholas Sparks',
               description='Noah is restoring a plantation home to its former glory, and he is haunted by images of the beautiful girl he met fourteen years earlier, a girl he loved like no other. Unable to find her, yet unwilling to forget the summer they spent together, Noah is content to live with only memories...until she unexpectedly returns to his town to see him once again.',
               release_date=datetime(day=5, month=6, year=1996),
               cover_url='https://images.gr-assets.com/books/1385738917l/15931.jpg',
               genre='R',

               complexity=2,
               nr_pages=214,
               popularity=10,
               humor=1,


                featureX=5,
                featureY=6
               )

    alice = make(Book,
               title='Alice\'s Adventures in Wonderland',
               short_name='Alice',
               author='Lewis Carroll',
               description='Weary of her storybook, one "without pictures or conversations," the young and imaginative Alice follows a hasty hare underground--to come face-to-face with some of the strangest adventures and most fantastic characters in all of literature. ',
               release_date=datetime(day=5, month=6, year=1865),
               cover_url='https://images.gr-assets.com/books/1391458382l/13023.jpg',
               genre='Fan',

               complexity=1,
               nr_pages=239,
               popularity=9,
               humor=4,

                featureX=5,
                featureY=8
               )

    fault = make(Book,
               title='The Fault in Our Stars',
               short_name='Stars',
               author='John Green',
               description='Despite the tumor-shrinking medical miracle that has bought her a few years, Hazel has never been anything but terminal, her final chapter inscribed upon diagnosis. But when a gorgeous plot twist named Augustus Waters suddenly appears at Cancer Kid Support Group, Hazel\'s story is about to be completely rewritten.',
               release_date=datetime(day=10, month=1, year=2012),
               cover_url='https://images.gr-assets.com/books/1360206420l/11870085.jpg',
               genre='R',

               complexity=2,
               nr_pages=313,
               popularity=7,
               humor=3,

                featureX=7,
                featureY=5
               )

    thief = make(Book,
               title='The Book Thief',
               short_name='BookThief',
               author='Markus Zusak',
               description='It’s just a small story really, about among other things: a girl, some words, an accordionist, some fanatical Germans, a Jewish fist-fighter, and quite a lot of thievery. . . .',
               release_date=datetime(day=5, month=6, year=2005),
               cover_url='https://images.gr-assets.com/books/1390053681l/19063.jpg',
               genre='SF',

               complexity=5,
               nr_pages=552,
               popularity=7,
               humor=2,

                featureX=3,
                featureY=2
               )

    harry1 = make(Book,
               title='Harry Potter and the Sorcerer\'s Stone',
               short_name='HP3',
               author='J. K. Rowling',
               description='Harry Potter\'s life is miserable. His parents are dead and he\'s stuck with his heartless relatives, who force him to live in a tiny closet under the stairs. But his fortune changes when he receives a letter that tells him the truth about himself: he\'s a wizard. ',
               release_date=datetime(day=5, month=6, year=1997),
               cover_url='https://images.gr-assets.com/books/1474154022l/3.jpg',
               genre='Fan',

               complexity=2,
               nr_pages=320,
               popularity=10,
               humor=4,

                featureX=6,
                featureY=6
               )

    hobbit = make(Book,
               title='The Hobbit',
               short_name='Hobbit',
               author='JRR Tolkein',
               description='In a hole in the ground there lived a hobbit. Not a nasty, dirty, wet hole, filled with the ends of worms and an oozy smell, nor yet a dry, bare, sandy hole with nothing in it to sit down on or to eat: it was a hobbit-hole, and that means comfort.',
               release_date=datetime(day=5, month=6, year=1937),
               cover_url='https://images.gr-assets.com/books/1372847500l/5907.jpg',
               genre='Fan',

               complexity=6,
               nr_pages=366,
               popularity=8,
               humor=4,

                featureX=2,
                featureY=9
               )

    romeo = make(Book,
               title='Romeo and Juliet',
               short_name='R&J',
               author='William Shakespeare',
               description='In Romeo and Juliet, Shakespeare creates a world of violence and generational conflict in which two young people fall in love and die because of that love. The story is rather extraordinary in that the normal problems faced by young lovers are here so very large.',
               release_date=datetime(day=5, month=6, year=1595),
               cover_url='https://images.gr-assets.com/books/1327872146l/18135.jpg',
               genre='R',

               complexity=3,
               nr_pages=283,
               popularity=9,
               humor=2,

                featureX=6,
                featureY=5
               )

    dorian = make(Book,
               title='The Picture of Dorian Grey',
               short_name='DorianGrey',
               author='Oscar Wilde',
               description='Written in his distinctively dazzling manner, Oscar Wilde’s story of a fashionable young man who sells his soul for eternal youth and beauty is the author’s most popular work. ',
               release_date=datetime(day=5, month=6, year=1890),
               cover_url='https://images.gr-assets.com/books/1424596966l/5297.jpg',
               genre='SF',

               complexity=5,
               nr_pages=254,
               popularity=6,
               humor=1,

                featureX=3,
                featureY=3
               )

    dracula = make(Book,
               title='Dracula',
               short_name='Dracula',
               author='Bram Stoker',
               description='A rich selection of background and source materials is provided in three areas: Contexts includes probable inspirations for Dracula in the earlier works of James Malcolm Rymer and Emily Gerard. ',
               release_date=datetime(day=5, month=6, year=1897),
               cover_url='https://images.gr-assets.com/books/1387151694l/17245.jpg',
               genre='SF',

               complexity=2,
               nr_pages=488,
               popularity=10,
               humor=1,

                featureX=4,
                featureY=3
               )

    gatsby = make(Book,
               title='The Great Gatsby',
               short_name='Gatsby',
               author='F. Scott Fitzgerald',
               description='The story of the fabulously wealthy Jay Gatsby and his love for the beautiful Daisy Buchanan, of lavish parties on Long Island at a time when The New York Times noted “gin was the national drink and sex the national obsession,” it is an exquisitely crafted tale of America in the 1920s.',
               release_date=datetime(day=5, month=6, year=1925),
               cover_url='https://images.gr-assets.com/books/1438728255l/4671.jpg',
               genre='R',

               complexity=3,
               nr_pages=180,
               popularity=8,
               humor=3,

                featureX=3,
                featureY=3
               )

    swift = make(Book,
                 title='The Swift Porgramming Language',
                 short_name='Swift',
                 author='Apple Inc',
                 description='Swift is a programming language for creating iOS, macOS, watchOS, and tvOS apps. Swift builds on the best of C and Objective-C, without the constraints of C compatibility.',
                 release_date=datetime(day=2, month=6, year=2014),
                 cover_url='https://images.gr-assets.com/books/1440784267l/26182448.jpg',
                 genre='Prog',

                 complexity=6,
                 nr_pages=250,
                 popularity=5,
                 humor=2,

                featureX=10,
                featureY=10
                 )

    hunger = make(Book,
                 title='The Hunger Games',
                 short_name='Hunger',
                 author='Suzanne Collins',
                 description='Winning will make you famous. Losing means certain death.',
                 release_date=datetime(day=14, month=9, year=2008),
                 cover_url='https://images.gr-assets.com/books/1447303603l/2767052.jpg',
                 genre='SF',

                 complexity=4,
                 nr_pages=374,
                 popularity=9,
                 humor=1,

                featureX=2,
                featureY=7
                 )

    potter = make(Book,
                 title='Harry Potter and The Order of the Phoenix',
                 short_name='HP5',
                 author='J. K. Rowling',
                 description='Harry Potter is due to start his fifth year at Hogwarts School of Witchcraft and Wizardry. His best friends Ron and Hermione have been very secretive all summer and he is desperate to get back to school and find out what has been going on. However, what Harry discovers is far more devastating than he could ever have expected...',
                 release_date=datetime(day=10, month=8, year=2004),
                 cover_url='https://images.gr-assets.com/books/1387141547l/2.jpg',
                 genre='Fan',

                 complexity=2,
                 nr_pages=870,
                 popularity=8,
                 humor=2,

                featureX=5,
                featureY=7
                 )

    pride = make(Book,
                 title='Pride and Prejudice',
                 short_name='P&P',
                 author='Jane Austen',
                 description='tells the story of Mr and Mrs Bennet\'s five unmarried daughters after the rich and eligible Mr Bingley and his status-conscious friend, Mr Darcy, have moved into their neighbourhood. "It is a truth universally acknowledged, that a single man in possession of a good fortune must be in want of a wife."',
                 release_date=datetime(day=10, month=6, year=2000),
                 cover_url='https://images.gr-assets.com/books/1320399351l/1885.jpg',
                 genre='SF',

                 complexity=4,
                 nr_pages=279,
                 popularity=7,
                 humor=2,

                featureX=2,
                featureY=3
                 )

    twilight = make(Book,
                 title='Twilight',
                 short_name='Twilight',
                 author='Stephnie Meyer',
                 description='In the first book of the Twilight Saga, internationally bestselling author Stephenie Meyer introduces Bella Swan and Edward Cullen, a pair of star-crossed lovers whose forbidden relationship ripens against the backdrop of small-town suspicion and a mysterious coven of vampires. This is a love story with bite.',
                 release_date=datetime(day=2, month=6, year=2014),
                 cover_url='https://images.gr-assets.com/books/1361039443l/41865.jpg',
                 genre='R',

                 complexity=2,
                 nr_pages=498,
                 popularity=8,
                 humor=3,

                featureX=7,
                featureY=6
                 )

    narnia = make(Book,
               title='The Chronicles Of Narnia',
               short_name='Narnia',
               author='C. S. Lewis',
               description='Set in the fictional realm of Narnia, a fantasy world of magic, mythical beasts, and talking animals, the series narrates the adventures of various children who play central roles in the unfolding history of that world. ',
               release_date=datetime(day=16, month=6, year=2002),
               cover_url='https://images.gr-assets.com/books/1449868701l/11127.jpg',
               genre='Fan',

               complexity=4,
               nr_pages=767,
               popularity=8,
               humor=3,

                featureX=4,
                featureY=8
               )

    davinci = make(Book,
               title='The Da Vinci Code',
               short_name='DaVinci',
               author='Dan Brown',
               description='An ingenious code hidden in the works of Leonardo da Vinci. A desperate race through the cathedrals and castles of Europe. An astonishing truth concealed for centuries . . . unveiled at last.',
               release_date=datetime(day=5, month=6, year=2006),
               cover_url='https://images.gr-assets.com/books/1303252999l/968.jpg',
               genre='SF',

               complexity=5,
               nr_pages=481,
               popularity=6,
               humor=1,

                featureX=4,
                featureY=3
               )

    geisha = make(Book,
               title='Memoirs of a Geisha',
               short_name='Geisha',
               author='Arthur Golden',
               description='In Memoirs of a Geisha, we enter a world where appearances are paramount; where a girl\'s virginity is auctioned to the highest bidder; where women are trained to beguile the most powerful men; and where love is scorned as illusion. It is a unique and triumphant work of fiction - at once romantic, erotic, suspenseful - and completely unforgettable.',
               release_date=datetime(day=5, month=6, year=2005),
               cover_url='https://images.gr-assets.com/books/1388367666l/930.jpg',
               genre='SF',

               complexity=5,
               nr_pages=430,
               popularity=7,
               humor=1,

                featureX=5,
                featureY=2
               )

    # miserables = make(Book,
    #            title='Les Miserables',
    #            short_name='Miserables',
    #            author='Victor Hugo',
    #            description='Introducing one of the most famous characters in literature, Jean Valjean - the noble peasant imprisoned for stealing a loaf of bread. In Les Misérables Victor Hugo takes readers deep into the Parisian underworld, immerses them in a battle between good and evil, and carries them onto the barricades during the uprising of 1832. ',
    #            release_date=datetime(day=5, month=6, year=1862),
    #            genre='SF',
    #
    #            complexity=5,
    #            nr_pages=1463,
    #            popularity=6,
    #            humor=1
    #            )

    # Users
    stefan = make(User,
                  username='stefan',
                  password='parola123',
                  email='stefan@google.com')
    alex = make(User,
                username='alex',
                password='parola123',
                email='alex@gmail.com')

    alexP = Profile.objects.get(user_id=alex.id)
    alexP.hashed_password = bcrypt.encrypt('alex', rounds=4)
    alexP.save()

    ade = make(User,
               username='ade',
               password='parola123',
               email='andreea@yahoo.com')

    # Loans
    stefan_lotr = make(Loan, user=stefan, book=lotr, start_date=datetime(day=22, month=9, year=2016, hour=19, minute=30), return_date=datetime(day=24, month=9, year=2016, hour=19, minute=30))
    stefan_sw = make(Loan, user=stefan, book=sw, start_date=datetime(day=22, month=9, year=2016, hour=19, minute=35))
    stefan_cormen = make(Loan, user=stefan, book=cormen, start_date=datetime(day=22, month=2, year=2016, hour=10, minute=0))

    alex_lotr = make(Loan, user=alex, book=lotr, start_date=datetime(day=22, month=10, year=2016, hour=19, minute=30), return_date=datetime(day=24, month=9, year=2016, hour=19, minute=30))
    alex_got = make(Loan, user=alex, book=got, start_date=datetime(day=22, month=10, year=2016, hour=18, minute=11))

    ade_swift = make(Loan, user=ade, book=swift, start_date=datetime(day=5, month=6, year=2016, hour=12, minute=0))
