package store

import (
	"jjs-server/internal/config"
	"jjs-server/internal/domain"
)

func GetHumanPlayerStates() ([]domain.PlayerState, error) {
	var ps []domain.PlayerState
	err := DB.Where("player_id NOT LIKE ? AND player_id != ?", "bot_%", config.SystemBrokerID).
		Find(&ps).Error
	return ps, err
}

func GetHoldingsByPlayerIDs(playerIDs []string) (map[string][]domain.Holding, error) {
	if len(playerIDs) == 0 {
		return map[string][]domain.Holding{}, nil
	}
	var holdings []domain.Holding
	err := DB.Where("player_id IN ?", playerIDs).Find(&holdings).Error
	if err != nil {
		return nil, err
	}
	result := make(map[string][]domain.Holding, len(playerIDs))
	for _, h := range holdings {
		result[h.PlayerID] = append(result[h.PlayerID], h)
	}
	return result, nil
}
