from shopping_list.models import User

alice = User.objects.create_user(username='alice', email='alice@test.com', password='foo')
bob = User.objects.create_user(username='bob', email='bob@test.com', password='foo')
charlie = User.objects.create_user(username='charlie', email='charlie@test.com', password='foo')

print('Succefully created users: ')
print('1.', alice)
print('2.', bob)
print('3.', charlie)
