package store

import (
	"crypto/rand"
	"encoding/hex"

	"golang.org/x/crypto/bcrypt"

	"jjs-server/internal/domain"
)

func GeneratePlayerID() string {
	b := make([]byte, 6)
	rand.Read(b)
	return hex.EncodeToString(b)
}

func HashPassword(password string) (string, error) {
	bytes, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	return string(bytes), err
}

func CheckPassword(hash, password string) bool {
	return bcrypt.CompareHashAndPassword([]byte(hash), []byte(password)) == nil
}

func CreateUser(username, password, nickname string) (*domain.User, error) {
	hash, err := HashPassword(password)
	if err != nil {
		return nil, err
	}
	user := &domain.User{
		ID:           GeneratePlayerID(),
		Username:     username,
		Nickname:     nickname,
		PasswordHash: hash,
	}
	if err := DB.Create(user).Error; err != nil {
		return nil, err
	}
	return user, nil
}

func GetUserByUsername(username string) (*domain.User, error) {
	var user domain.User
	err := DB.Where("username = ?", username).First(&user).Error
	if err != nil {
		return nil, err
	}
	return &user, nil
}

func GetUserByID(id string) (*domain.User, error) {
	var user domain.User
	err := DB.Where("id = ?", id).First(&user).Error
	if err != nil {
		return nil, err
	}
	return &user, nil
}

func UpdateUserNickname(userID, nickname string) error {
	return DB.Model(&domain.User{}).Where("id = ?", userID).Update("nickname", nickname).Error
}
