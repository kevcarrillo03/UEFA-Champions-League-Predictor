import pandas as pd
import xgboost as xgb
from sklearn.metrics import accuracy_score, log_loss, classification_report
import joblib
from pathlib import Path
import json

processed_data_dir = Path("data/processed")
models_dir = Path("models")
models_dir.mkdir(parents=True, exist_ok=True)

def train_model():
    matrix_path = processed_data_dir / "training_matrix.csv"

    df = pd.read_csv(matrix_path)

    #ensures chron order
    df['match_date'] = pd.to_datetime(df['match_date'])
    df = df.sort_values('match_date').reset_index(drop=True)

    print(f"loaded {len(df)} matches")

    #dropping string identifiers and anything model wouldnt know before kickoff
    drop_cols = [
        'match_id', 'match_date', 'stage', 
        'home_team', 'away_team', 'home_country', 'away_country',
        'home_goals', 'away_goals', 'target'
    ]

    x = df.drop(columns=[col for col in drop_cols if col in df.columns])
    y = df['target'] #0=away win , 1 = draw, 2=home win

    #training on first 80% of the matches then testing on final 20
    split_index = int(len(df)* 0.8)

    x_train, x_test = x.iloc[:split_index], x.iloc[split_index:]
    y_train, y_test = y.iloc[:split_index], y.iloc[split_index:]

    print(f"training on {len(x_train)} historical matches...")
    print(f"testing on {len(x_test)} future matches...")

    #train xgboost classifier

    model = xgb.XGBClassifier(
        objective='multi:softprob',
        num_class=3,
        learning_rate=0.05,
        max_depth=4,       #kept it shallow to prevent overfitting on sports data
        n_estimators=150,
        eval_metric='mlogloss',
        random_state=42
    )

    model.fit(x_train,y_train)

    print("\n2. evaluating model")

    y_pred_proba = model.predict_proba(x_test)
    y_pred = model.predict(x_test)
    accuracy = accuracy_score(y_test, y_pred)
    loss = log_loss(y_test, y_pred_proba)
    baseline_accuracy = (y_test == 2).mean() #baseline what if home team just always won

    print(f"model accuracy:      {accuracy * 100:.2f}%")
    print(f"baseline (home win): {baseline_accuracy * 100:.2f}%")
    print(f"log loss:            {loss:.4f}")

    print("\nclassification report:")
    print(classification_report(y_test, y_pred, target_names=['Away Win (0)', 'Draw (1)', 'Home Win (2)']))

    feature_importance = pd.DataFrame({
        'Feature': x.columns,
        'Importance': model.feature_importances_
    }).sort_values('Importance', ascending=False)
    
    print("\ntop 5 most important features:") #what the model cares about
    print(feature_importance.head(5).to_string(index=False))

    model_path = models_dir/ "xgb_match_predictor.pkl"
    joblib.dump(model, model_path)

    #feature column name for sim
    features_path = models_dir / "model_feature.json"
    with open(features_path, "w") as f:
        json.dump(list(x.columns),f)

    print(f"model saved to {model_path}")

if __name__ == "__main__":
    train_model()
