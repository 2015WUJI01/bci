package store

import (
	"jjs-server/internal/domain"
)

func MaxProsperityQuarter() (int, error) {
	var maxQ int
	err := DB.Model(&domain.IndustryProsperity{}).
		Select("COALESCE(MAX(quarter), 0)").
		Scan(&maxQ).Error
	return maxQ, err
}

func ProsperityExists(industry string, quarter int) (bool, error) {
	var count int64
	err := DB.Model(&domain.IndustryProsperity{}).
		Where("industry = ? AND quarter = ?", industry, quarter).
		Count(&count).Error
	return count > 0, err
}

func SaveProsperity(industry string, quarter int, prosperity float64) error {
	return DB.Create(&domain.IndustryProsperity{
		Industry:   industry,
		Quarter:    quarter,
		Prosperity: prosperity,
	}).Error
}

func LatestProsperity(industry string) (float64, error) {
	var p domain.IndustryProsperity
	err := DB.Where("industry = ?", industry).
		Order("quarter DESC").
		First(&p).Error
	if err != nil {
		return 1.0, err
	}
	return p.Prosperity, nil
}

func ProsperityHistory(industry string, limit int) ([]domain.IndustryProsperity, error) {
	var rows []domain.IndustryProsperity
	err := DB.Where("industry = ?", industry).
		Order("quarter DESC").
		Limit(limit).
		Find(&rows).Error
	return rows, err
}
