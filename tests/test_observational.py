import numpy as np
import pandas as pd
from src.pbf.observational import PREDICTORS, RF_CONFIG, load_fold_data, validate_folds, fit_rf, predict_rf
from workflows.observational.diagnostics import TREE_COUNTS

def make_inputs(tmp_path):
    rows=[]
    for fold in range(1,41):
        left=1980+fold
        for year in range(1981,2021):
            if year != left: rows.append({"Fold":fold,"Left_Out_Year":left,"Train_Year":year,**{p:float(year-fold) for p in PREDICTORS}})
    pd.DataFrame(rows).to_csv(tmp_path/"fold.csv", index=False)
    pd.DataFrame({"year":range(1981,2021),"recruitment":np.arange(11,51)}).to_csv(tmp_path/"recruitment.csv", index=False)
    return tmp_path/"fold.csv", tmp_path/"recruitment.csv"

def test_fold_validation_and_alignment(tmp_path):
    fold, recruitment = make_inputs(tmp_path); data = load_fold_data(fold, recruitment); validate_folds(data)
    assert list(PREDICTORS) == ["PO_PC1","AO_PC1","PO_PC2","AO_PC2","PO_PC3","AO_PC3"]
    assert data.recruitment.notna().all()

def test_rf_reproducibility_and_future_vector(tmp_path):
    fold, recruitment = make_inputs(tmp_path); data = load_fold_data(fold, recruitment); group=data[data.Fold==1]
    X=group.loc[:,PREDICTORS].to_numpy(); y=np.log10(group.recruitment.to_numpy())
    first,_=fit_rf(X,y); second,_=fit_rf(X,y)
    assert np.allclose(predict_rf(first, X[:1]), predict_rf(second, X[:1]))
    assert predict_rf(first, np.zeros((1,6))).shape == (1,)
    assert first.get_params()["random_state"] == RF_CONFIG["random_state"]

def test_diagnostic_tree_counts_and_dimensions():
    assert TREE_COUNTS == (100, 200, 500, 1000)
    assert len(PREDICTORS) == 6
