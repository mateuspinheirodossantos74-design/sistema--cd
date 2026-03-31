import bcrypt

senha = "cd@1200"

hash_senha = bcrypt.hashpw(
    senha.encode(),
    bcrypt.gensalt()
).decode()

print(hash_senha)
